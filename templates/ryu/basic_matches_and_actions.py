from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3, inet
from ryu.lib.packet import packet, ethernet, ipv4, udp, arp, ether_types, vlan, tcp, icmp


class TemplateRyuApp(app_manager.RyuApp):
    """
    A minimal Ryu app that logs packet-in events and installs a table-miss flow.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]  # Use OpenFlow 1.3

    def __init__(self, *args, **kwargs):
        """
        Initialize the Ryu app and any necessary variables.
        """
        super(TemplateRyuApp, self).__init__(*args, **kwargs)

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


    def match_template_showcase(self, datapath):
        """
        This method is NOT meant to be used directly.
        This is intended to show you a list of examples of how you can use the OFPMatch object!

        You can copy the match blocks you need and use them with install_flow() in your own code :)

        These are a collection of DIFFERENT matches. You only have ONE match you use with a flow in a real world environment.
        With that said, you can combine multiple parts of them together.
        I.e., an ipv4_src, ipv4_dst, udp_dst, vlan id, etc
        """
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Example 1. Match packets FROM a specific IP address
        match_src_ip = parser.OFPMatch(
            eth_type=0x0800,          # IPv4 packets only
            ipv4_src="10.0.0.1"
        )

        # Example 2. Match packets TO a specific IP address
        match_dst_ip = parser.OFPMatch(
            eth_type=0x0800,
            ipv4_dst="10.0.0.2"
        )

        # Example 3. Match TCP packets FROM source port 22
        match_tcp_src_port = parser.OFPMatch(
            eth_type=0x0800,
            ip_proto=6,              # TCP
            tcp_src=22
        )

        # Example 4. Match TCP packets TO destination port 443
        match_tcp_dst_port = parser.OFPMatch(
            eth_type=0x0800,
            ip_proto=6,              # TCP
            tcp_dst=443
        )

        # Example 5. Match UDP packets FROM source port 53
        match_udp_src_port = parser.OFPMatch(
            eth_type=0x0800,
            ip_proto=17,             # UDP
            udp_src=53
        )

        # Example 6. Match packets FROM a specific MAC address
        match_mac = parser.OFPMatch(
            eth_src="00:11:22:33:44:55"
        )

        # Example 7. Match packets tagged with VLAN ID 100
        match_vlan = parser.OFPMatch(
            vlan_vid=100
        )

        # Example 8. Match ARP request packets
        match_arp = parser.OFPMatch(
            eth_type=0x0806,         # ARP
            arp_op=1                 # 1 = Request, 2 = Reply
        )

        # Example 9. Combination of multiple different potential matches
        # You can make any type of combination you like :)
        match_multiple = parser.OFPMatch(
            eth_type=0x0800,        # IPV4
            ip_proto=17,            # UDP Packet
            ipv4_dst='1.1.1.1',     # IP Address of 1.1.1.1
            udp_dst=7777            # UDP Port 7777
        )

        #Example 10. Match everything
        match_everything = parser.OFPMatch()



        # All of these can be used like this:
        # self.install_flow(datapath, priority=10, match=match_tcp_dst_port, actions=actions) - Note you would also have to create the actions list! (refer to actions_template_showcase)


    def actions_template_showcase(self, datapath):
        """
        This method is NOT meant to be used directly.
        This is intended to show you a list of examples of how you can use the OFPAction* objects!

        You can copy the action variables you need and use them with install_flow() in your own code :)

        Each of the following is ONE action. You can then combine them into a list (shown at the bottom).
        """

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Example 1. Send the packet OUT a specific port (e.g., Port 1)
        action_output_port_1 = parser.OFPActionOutput(1) # You can obviously change to 2/3/4/5/6/7/8/9 beyond also! :)

        # Example 2. Send the packet TO the controller
        action_output_to_controller = parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)

        # Example 3. Flood the packet to all ports except the one it came in on
        action_flood = parser.OFPActionOutput(ofproto.OFPP_FLOOD)

        # Example 4. Change the Destination MAC address
        action_set_dst_mac = parser.OFPActionSetField(eth_dst="aa:bb:cc:dd:ee:ff") # Source equivalent is obviously eth_src

        # Example 5. Remove the VLAN tag from a packet (if present)
        action_strip_vlan = parser.OFPActionPopVlan()

        # Example 6. Add a VLAN tag to an untagged packet (VLAN 300)
        # Remember to include BOTH in your actions list if you want to properly set the VLAN.
        action_push_vlan = parser.OFPActionPushVlan(ether_types.ETH_TYPE_8021Q)
        action_set_vlan_300 = parser.OFPActionSetField(vlan_vid=300)

        # Example 7. Change the Destination IP address
        action_set_dst_ip = parser.OFPActionSetField(ipv4_dst="192.168.1.100") # Source equivalent is obviously ipv4_src

        # Example 8. Change the UDP Destination Port
        action_set_tcp_dst_port = parser.OFPActionSetField(tcp_dst=1005) # Source equivalent is obviously udp_src

        # Combine multiple actions together to make the actions list like this:
        actions = [action_set_dst_mac, action_output_port_1]

        # If you want to DROP the packet (do nothing):
        actions = []

        # After you have made the actions list, you can then install the flow, as per the following:
        # self.install_flow(datapath, priority=10, match=match, actions=actions) - Note you would also have to create the match object! Refer to the match_template_showcase method :)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Called when a switch first connects. Installs a default rule to send unmatched packets to the controller.
        """
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto


        # Refer to actions_template_showcase to find different ways to use the OFPMatch object
        # In this example, however, it matches everything.
        match = parser.OFPMatch()

        # Refer to actions_template showcase to find different ways to use the actions list
        # In this example, however, it OUTPUTS to the CONTROLLER.
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        self.install_flow(datapath, priority=0, match=match, actions=actions)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles packets sent to the controller.

        This function is triggered every time a switch sends a packet to the controller
        """
        return # No need to use this method in this example script! :)
