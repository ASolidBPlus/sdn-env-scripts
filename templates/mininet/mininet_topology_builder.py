from utils.mininet.helpers import createInitialNetwork, safeMininetStartupAndExit

# ╔══════════════════════════════════════════════╗
# ║              TOPOLOGY DEFINITIONS            ║
# ╚══════════════════════════════════════════════╝
# These are the network topologies you can actually launch in Mininet.
# Copy/paste templateTopology(), rename it, and modify it to make your own.
# Then scroll to the bottom and register it in the 'topos' dictionary.

def basicExampleTopology():
    net = createInitialNetwork()

    # Add hosts with set IPs
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='192.168.1.1/24')

    # Add a switch
    s1 = net.addSwitch('s1')

    # Connect hosts to switch
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1, loss=10)  # Add 10% packet loss just for fun/testing

    # This always needs to be added, otherwise the network simulatiion won't start.
    net.start()

    # IMPORTANT: Don't run post-launch logic (e.g. ping, cmd) until net.start() has been called!
    print("\nPing between h1 and h2:")
    net.ping([h1, h2])
    print("\nPing between h1 and h3 (different subnets):")
    net.ping([h1, h3])

    safeMininetStartupAndExit(net)


def advancedExampleTopology():
    net = createInitialNetwork()

    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')

    # If you add switches with the traditional naming scheme of s1/s2/s3, it adds a 'DPID' sequentially automatically.
    # The DPID is important as it can be used to identify your switch in an SDN Program. I.e., "if DPID == 1, then do xyz"

    s1 = net.addSwitch('s1') # This will give the DPID of '1'

    # HOWEVER, unique switch names requires a bit of extra configuration. You need to manually specify the DPID yourself.

    leaf1 = net.addSwitch('leaf1', dpid='2') # We start from 2 because s1 already has the DPID of 1.
    leaf2 = net.addSwitch('leaf2', dpid='3')
    spine = net.addSwitch('spine', dpid='4')

    net.addLink(leaf1, spine)
    net.addLink(h1, leaf1)

    net.addLink(leaf2, spine)

    # This always needs to be added, otherwise the network simulatiion won't start.
    net.start()

    # You can run specific commands on a host device, as if it's a real computer.
    # Much like pings, this can only be done after net.start() has been called.

    # Example of setting a static ARP entry manually
    h1.cmd("arp -s 10.0.0.2 00:00:00:00:00:02")


    safeMininetStartupAndExit(net)


def oneSwitchThreeHost():
    net = createInitialNetwork()

    # Basic 3-host, 1-switch setup
    s1 = net.addSwitch('s1')
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')

    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)

    net.start()
    safeMininetStartupAndExit(net)

def threeSwitchThreeHost():
    net = createInitialNetwork()

    # A small spine-like topology across 3 switches
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')

    net.addLink(h1, s1)
    net.addLink(s1, s2)
    net.addLink(h2, s2)
    net.addLink(s2, s3)
    net.addLink(h3, s3)

    net.start()
    safeMininetStartupAndExit(net)

def templateTopology():
    """
    This one’s a blank slate.
    Copy it, rename it, and build from here.

    IMPORTANT:
    - Always start with net = createInitialNetwork()
    - Always end with safeMininetStartupAndExit(net)
    - You MUST call net.start() before any post-launch commands like ping or arp
    - Refer to the other pre-existing topology methods for examples of how they can be configured.
    """
    net = createInitialNetwork()

    # Add devices/links here

    net.start()

    # Do post-start commands here (e.g. pings, route config, ARP setup)

    safeMininetStartupAndExit(net)

# ╔══════════════════════════════════════════════╗
# ║              TOPOLOGY REGISTRATION           ║
# ╚══════════════════════════════════════════════╝
# This dictionary lets you run your topologies from the terminal using --topo.
# It maps a name you choose (on the left) to the actual function that builds the network (on the right).
#
# For example, if you create a function like:
#   def starTopology():
# And want to launch it with:
#   sudo mn --custom ~/Documents/SDN\ Scripts/mininet_custom_helper.py --topo star
# You’d need to add this line:
#   'star': (lambda: starTopology())
#
# Left side = the name you type after --topo
# Right side = the function that sets up the network (wrapped in lambda)

topos = {
    'basicExample': (lambda: basicExampleTopology()),
    'advancedExample': (lambda: advancedExampleTopology()),
    '1Switch3Host': (lambda: oneSwitchThreeHost()),
    '3Switch3Host': (lambda: threeSwitchThreeHost())
    # Add your own as needed
}