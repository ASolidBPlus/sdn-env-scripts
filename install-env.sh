#!/usr/bin/env bash
set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# 1. Install code-server and configure on port 8081
# -----------------------------------------------
# Download & install
curl -fsSL https://code-server.dev/install.sh | sh

# 1.1. Configure code-server password
mkdir -p /home/student/.config/code-server
cat <<EOF >/home/student/.config/code-server/config.yaml
bind-addr: 0.0.0.0:8081
auth: password
password: student
cert: false
EOF
chown -R student:student /home/student/.config/code-server

# Create workspace and set ownership
mkdir -p /opt/scripts
chown student:student /opt/scripts

# Disable default service
systemctl disable --now code-server@student

# Override systemd unit for port & workspace
mkdir -p /etc/systemd/system/code-server@student.service.d
cat <<EOF >/etc/systemd/system/code-server@student.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/bin/code-server --bind-addr 0.0.0.0:8081 /opt/scripts
WorkingDirectory=/opt/scripts
EOF

# Reload, enable & start
systemctl daemon-reload
systemctl enable --now code-server@student

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
$1

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
mkdir -p /opt/dep
cd /opt/dep
git clone https://github.com/martimy/flowmanager.git flowmanager
chown -R student:student /opt/dep/flowmanager

echo "FlowManager installed at /opt/dep/flowmanager"

