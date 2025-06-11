from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3, inet
from ryu.lib.packet import packet, ethernet, ipv4, udp, arp, ether_types

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
        
        # The two potential round-robin options, used alongside self.get_port_option()
        self.port_options = [
            {'port': 2, 'ip_address': '10.0.0.101'}, 
            {'port': 3, 'ip_address': '10.0.0.102'}
        ]

        self.current_port = 0

    def get_port_option(self):
        """
        Provides the current option from self.port_options, then toggles self.current_port
        between 0 and 1 for the next call.
        """
        option = self.port_options[self.current_port]
        self.current_port = 1 - self.current_port
        return option

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Method called when Switch first connects to the Ryu Controller. Used to add initial flow tables.
        """

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # NOTE: This week's controller is quite a bit more complicated — it requires multiple flows to be installed on the switch.
        # Follow the TODO comments for guidance on the 'match' and 'actions' you need to define.
        # All the logic is in place — you just need to write the correct syntax.
        # Refer to last week’s helper .py files from the Week 12 practical, and this week’s lecture Ryu controller for examples.

        # FLOW 1 – Priority: 2
        self.logger.info(
            "FLOW 1 (priority 2):\n"
            "  Match destination IP 10.0.0.100\n"
            "  ACTION: OUTPUT -> CONTROLLER"
        )
        match = parser.OFPMatch()  # TODO: Match IP traffic with dst IP = 10.0.0.100
        actions = []               # TODO: OUTPUT -> CONTROLLER

        self.install_flow(datapath, 2, match, actions)

        # FLOW 2 – Priority: 1
        self.logger.info(
            "FLOW 2 (priority 1):\n"
            "  Match source IP 10.0.0.101\n"
            "  ACTION: Set IPv4 src to 10.0.0.100\n"
            "          OUTPUT -> NORMAL"
        )
        match = parser.OFPMatch()  # TODO: Match IP traffic with src IP = 10.0.0.101
        actions = []               # TODO: Two actions required: (1) Set IPv4 src to 10.0.0.100, (2) OUTPUT -> NORMAL

        self.install_flow(datapath, 1, match, actions)

        # FLOW 3 – Priority: 1
        self.logger.info(
            "FLOW 3 (priority 1):\n"
            "  Match source IP 10.0.0.102\n"
            "  ACTION: Set IPv4 src to 10.0.0.100\n"
            "          OUTPUT -> NORMAL"
        )
        match = parser.OFPMatch()  # TODO: Match IP traffic with src IP = 10.0.0.102
        actions = []               # TODO: Two actions required: (1) Set IPv4 src to 10.0.0.100, (2) OUTPUT -> NORMAL

        self.install_flow(datapath, 1, match, actions)

        # FLOW 4 – Priority: 0
        self.logger.info(
            "FLOW 4 (priority 0):\n"
            "  Match all traffic\n"
            "  ACTION: OUTPUT -> NORMAL"
        )
        match = parser.OFPMatch()  # TODO: Match all traffic (leave empty)
        actions = []               # TODO: OUTPUT -> NORMAL

        self.install_flow(datapath, 0, match, actions)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles packets sent to the controller and prints basic info.
        """
        msg = ev.msg
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)  # Parse the raw packet data
        switch_id = datapath.id

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser


        self.logger.info(
        f"PACKET-IN HANDLER TRIGGERED BY SWITCH ID: {switch_id}:\n" # NOTE: Remember, you can use the switch_id in if statements if you want to have different flows for different switches
        "  Received a packet targeting 10.0.0.100\n"
        "  Round robin will decide which backend host to forward to"
    )

        # ROUND ROBIN TARGET SELECTION
        # TODO: Call self.get_port_option() to get the next backend IP + port
        selected = None  #NOTE If you call self.get_port_option() it'll give a dictionary with a structure that looks like this: {'port': 2, 'ip_address': '10.0.0.101'}

        # BUILD MATCH
        # TODO: Match IP traffic with dst IP = 10.0.0.100
        match = parser.OFPMatch()

        # BUILD ACTIONS
        # TODO: Three actions required:
        #   1. Set destination IP to selected['ip_address']
        #   2. Set destination MAC to ff:ff:ff:ff:ff:ff
        #   3. OUTPUT -> selected['port']
        actions = []

        # INSTALL FLOW
        self.logger.info(
            "INSTALLING TEMPORARY FLOW:\n"
            f"  -> dst IP becomes {selected['ip_address']}\n"
            f"  -> forwarding out port {selected['port']}\n"
            "  -> hard_timeout = 10 seconds\n"
            "  -> priority = higher than base flows"
        )

        # TODO: Install the flow using self.install_flow()
        #       Set hard_timeout=10, priority=3



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

