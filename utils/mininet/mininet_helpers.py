from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController, DefaultController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.term import makeTerm
import mininet.clean
import subprocess
import socket
import sys

# ╔══════════════════════════════════════════════╗
# ║                HELPER FUNCTIONS              ║
# ╚══════════════════════════════════════════════╝
# These handle setup, cleanup, and controller logic.

# These are just helper methods to make your life is easier.
# You don’t need to touch these – they just help Mininet behave a bit nicer.
# Go to the TOPOLOGY DEFINITIONS section for code relevant to you! :)

def controllerReachableCheck(ip, port):
    """Checks if the controller is up and accepting connections on the specified IP/port.
    You don’t need to care about this logic if unless you’re debugging controller startup. Ignore this!
    """
    try:
        with socket.create_connection((ip, port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def createInitialNetwork():
    """
    Sets up the base Mininet network object and optionally connects to an SDN controller.
    Also renames the terminal tab to 'Mininet Controller'.
    """
    # Set terminal tab title
    sys.stdout.write('\033]0;Mininet Controller\007')
    sys.stdout.flush()

    net = Mininet(link=TCLink, switch=OVSSwitch, controller=None)

    if input("Do you want to connect to an SDN Controller? Y/N: ").strip().lower() == 'y':
        ip = '127.0.0.1'
        port = 6633

        if controllerReachableCheck(ip, port):
            print("Controller is reachable, adding it now.")
            net.addController(RemoteController('c0', ip=ip, port=port))
        else:
            net.stop()
            mininet.clean.cleanup()
            print("Controller couldn’t be reached. Is ryu-manager running?")
            print("Network shutdown. Try again when it’s online.")
            quit()
    else:
        net.addController(DefaultController('c0'))

    return net


def safeMininetStartupAndExit(net):
    """
    Starts Mininet with the CLI and shuts everything down cleanly when you’re done.

    Always put this at the bottom of your topology method.

    Example usage: safeMininetStartupAndExit(net)
    """
    CLI(net)
    net.stop()
    mininet.clean.cleanup()
    print("Mininet shutdown complete. If ryu-manager was running, make sure to restart it before re-launching mininet.")
    sys.exit()