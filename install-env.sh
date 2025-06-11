#!/usr/bin/env bash
set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# 0) Pre-create environment directories
echo "Creating workspace and template directories..."
mkdir -p /opt/workspace /opt/templates /opt/utils /opt/workspace/ryu

# Set ownership & permissions
chown root:root /opt/templates
chmod 755 /opt/templates
chown student:student /opt/workspace /opt/workspace/ryu

# 1) Install code-server and configure on port 8081
# ------------------------------------------------
echo "Installing code-server..."
curl -fsSL https://code-server.dev/install.sh | sh

# 1.1) Configure code-server password and workspace
CONFIG_DIR="/home/student/.config/code-server"
WORKSPACE_FILE="/home/student/SDN Dev Environment.code-workspace"

echo "Creating code-server config and workspace file..."
mkdir -p "$CONFIG_DIR"
cat <<EOF > "$CONFIG_DIR/config.yaml"
bind-addr: 0.0.0.0:8081
auth: password
password: student
cert: false
EOF
chown -R student:student "$CONFIG_DIR"

# Create a multi-root VS Code workspace including /opt/workspace and /opt/templates
cat <<EOF | sudo -u student tee "$WORKSPACE_FILE" > /dev/null
{
  "folders": [
    { "path": "/opt/workspace" },
    { "path": "/opt/templates" },
    { "path": "/opt/utils" }
  ],
  "settings": {}
}
EOF
chown student:student "$WORKSPACE_FILE"

# Disable default service
systemctl disable --now code-server@student

# Override systemd unit to launch code-server with our workspace\mkdir -p /etc/systemd/system/code-server@student.service.d
mkdir -p /etc/systemd/system/code-server@student.service.d
cat <<EOF >/etc/systemd/system/code-server@student.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/bin/code-server --bind-addr 0.0.0.0:8081 "$WORKSPACE_FILE"
WorkingDirectory=/opt/workspace
EOF

# Reload, enable & start code-server
systemctl daemon-reload
systemctl enable --now code-server@student

echo "Code-server is running at http://<host-ip>:8081 using workspace 'SDN Dev Environment'"

# 2. Add deadsnakes PPA & install Python 3.9 + distutils
# ------------------------------------------------------
apt update
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.9 python3.9-venv python3.9-distutils

# 3. Create a venv at /opt/dep/ryu39
# --------------------------------
mkdir -p /opt/dep/ryu39
python3.9 -m venv /opt/dep/ryu39
chown -R student:student /opt/dep/ryu39

# 4. Activate venv & install Eventlet + Ryu
# ----------------------------------------
source /opt/dep/ryu39/bin/activate
pip install --upgrade pip setuptools==65.5.0 wheel
pip uninstall -y eventlet || true
pip install eventlet==0.30.2 ryu
deactivate

# 5. Register ryu-manager globally
# -------------------------------
update-alternatives --install /usr/bin/ryu-manager ryu-manager \
  /opt/dep/ryu39/bin/ryu-manager 100

# 6. Verify installation
# ----------------------
echo -n "ryu-manager location: "; which ryu-manager
echo -n "ryu-manager version:  "; ryu-manager --version

echo "\nSetup complete!"
echo "- Code-server: http://<host-ip>:8081 (pwd in ~/.config/code-server/config.yaml)"

# 7. Install Mininet from source (full)
# -------------------------------------
apt update
apt install -y git build-essential python3-pip python3-setuptools python3-dev
mkdir -p /opt/dep
cd /opt/dep
if [ ! -d mininet ]; then
  git clone https://github.com/mininet/mininet
fi
cd mininet
# -a installs Mininet, Open vSwitch, POX, Wireshark, etc.
util/install.sh -a

echo "Verifying Mininet installation..."
mn --test pingall

echo "Done! Mininet is installed."

# 8. Install FlowManager into /opt/dep
# -------------------------------------
mkdir -p /opt/dep
cd /opt/dep
git clone https://github.com/martimy/flowmanager.git flowmanager
chown -R student:student /opt/dep/flowmanager

echo "FlowManager installed at /opt/dep/flowmanager"


# 9. Caddy reverse-proxy  (port 81)
echo "Installing Caddy…"
apt install -y debian-keyring debian-archive-keyring curl gnupg apt-transport-https
if [ ! -f /usr/share/keyrings/caddy-stable-archive-keyring.gpg ]; then
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | \
    gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
fi
echo "deb [signed-by=/usr/share/keyrings/caddy-stable-archive-keyring.gpg] \
https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" \
  | tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null

apt update
apt install -y caddy

echo "Writing Caddyfile…"
cat > /etc/caddy/Caddyfile <<'EOF'
:81 {
  # Serve static dashboard at /
  handle_path /index.html {
    root * /var/www
    file_server
  }

  handle_path / {
    root * /var/www
    try_files {path} /index.html
    file_server
  }

  # /code/* → code-server on 8081
  handle_path /code/* {
    reverse_proxy localhost:8081
  }

  # redirect bare /flowmanager → /flowmanager/
  @noSlash path /flowmanager
  handle @noSlash {
    redir /flowmanager/ 302
  }

  # /flowmanager/* → /home/* on FlowManager server
  handle_path /flowmanager/* {
    rewrite * /home{path}
    reverse_proxy localhost:8080
  }

  # catch-all: everything else → FlowManager
  handle {
    reverse_proxy localhost:8080
  }
}
EOF

# make sure caddy can bind low ports
setcap 'cap_net_bind_service=+ep' /usr/bin/caddy

systemctl restart caddy
echo "Caddy reverse-proxy live on http://<host-ip>:81"

# 10. Install extras
sudo apt install cron nano iputils-ping

# 11. Install update-env script for future updates
# -----------------------------------------------
if [ -f "$(dirname "$0")/bin/update-env" ]; then
  echo "Installing update-env..."
  sudo install -m 755 "$(dirname "$0")/bin/update-env" /usr/local/bin/update-env
  echo "You can now run 'update-env' to pull templates, bins, and utils."

  # Ask to schedule on startup
  read -p "Would you like to schedule update-env to run on every boot? [y/N] " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    (crontab -l 2>/dev/null; echo "@reboot /usr/local/bin/update-env") | crontab -
    echo "Scheduled update-env to run at startup via cron."
  fi

  # Ask to run now
  read -p "Run update-env now? [y/N] " ans2
  if [[ "$ans2" =~ ^[Yy]$ ]]; then
    /usr/local/bin/update-env
  fi
else
  echo "Warning: update-env script not found in bin/. Skipping update-env install." >&2
fi
