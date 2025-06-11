from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3, inet
from ryu.lib.packet import packet, ethernet, ipv4, udp, arp, ether_types
from ryu_maze import Maze

class TemplateRyuApp(app_manager.RyuApp):
    """
    A minimal Ryu app that logs packet-in events and installs a table-miss flow.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]  # Use OpenFlow 1.3

    def __init__(self, *args, **kwargs):
        """
        Initialize the Ryu app and any necessary variables.
        """
        # As "TemplateRyuApp" is inheriting from "app_manager.RyuApp", this is effectively 'creating' the data structure inherited from "app_manager.RyuApp"
        # This will make some sense if you have done Object Oriented Programming. If not, don't worry! It's not a necessity to completely understand this :)
        super(TemplateRyuApp, self).__init__(*args, **kwargs)
        self.maze = Maze()
        # self.maze.start()

    def install_flow(self, datapath, priority, match, actions=[], table_id=0, goto_table=None, idle_timeout=0, hard_timeout=0):
        """
        Use to install a flow on a switch.

        datapath: The datapath of the switch
        priority: Higher priority will appear higher on flow table, and more likely to be matched.
        match: The OFPMatch object that will be used.
        actions: A list of match options
        table_id: The table id that will be used, only necessary if you have multiple tables.
        goto_table: If you want to continue processing after finishing your actions, you can go to another table. This will specify the table id.
        idle_timeout: (seconds) how long until the network device deletes the flow
        hard_timeout: (seconds) how long period until the flow is deleted, regardless of how long it is being used.

        Note: For the most part, you will only need to worry about providing the datapath, priority, match (most important) and actions (most important). Only modify the others if need be.
        This is a template function, you should not be modifying this.
        """
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Create a list of instructions
        instructions = []

        # If actions are found (i.e., the actions list is not blank), wrap them as instructions
        # This creates a list of instructions that effectively says to 'apply' the action
        if actions:
            instructions.append(parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions))

        # If the goto_table variable set, apply the Goto Table
        if goto_table is not None:
            instructions.append(parser.OFPInstructionGotoTable(goto_table))

        # Create the flow mod message
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions,
            table_id=table_id,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )

        # Send the flow mod message to the switch
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Method called when Switch first connects to the Ryu Controller. Used to add initial flow tables.
        """
        
        # First, lets create the datapath object
        datapath = ev.msg.datapath

        switch_id = datapath.id # The DPID - Can be used if you want specific flows for specific switches (i.e., if DPID == 1, give xyz flow)

        self.logger.info("{switch_id} is requesting flows, providing a flow to Match Everything and OUTPUT to the CONTROLLER...")

        # Then, you want to create your parser and ofproto objects
        # A helper object that helps you create data structures used in flows, such as an OFPMatch or OFPActionOutput object
        parser = datapath.ofproto_parser
        
        # A helper object that provides you variables used to write a message. For example, you can use it to specify you want to OUTPUT to a CONTROLLER (see below)
        ofproto = datapath.ofproto 

        # ADD CODE HERE

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles packets sent to the controller and prints basic info.
        """
        msg = ev.msg
        datapath = msg.datapath

        # Parses the RAW Data into readable Packet Data
        pkt = packet.Packet(msg.data)

        # Gets the IPv4 Data from the Packet
        # This will only work if it is an IPv4 Packet.
        # If the event receives an ARP Request instead, as an example, this variable will return None
        # Refer to basic_ipv4_vlan_and_arp_variables.py under Week 12 > Practical for additional examples of what you can get from these variables.
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        # If it's an IPv4 Packet
        if ip_pkt:
            
            # Provides the Source and Destination IP as strings
            # You can use these in if statements, i.e., if destination_ip == '10.0.0.1':
            source_ip = ip_pkt.src
            destination_ip = ip_pkt.dst
            
            # ADD CUSTOM LOGIC HERE #
            



