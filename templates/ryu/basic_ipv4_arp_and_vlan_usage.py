from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3, inet
from ryu.lib.packet import packet, ethernet, ipv4, udp, arp, ether_types, vlan, tcp

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

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Called when a switch first connects. Installs a default rule to send unmatched packets to the controller.
        """
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        self.logger.info("Switch %s connected. Installing table-miss flow...", datapath.id)

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]

        self.install_flow(datapath, priority=0, match=match, actions=actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles packets sent to the controller.

        This function is triggered every time a switch sends a packet to the controller
        (because it didn’t know what to do with it yet — usually due to the table-miss flow).

        For this template, we just print useful details about the packet for learning/debugging.
        """
        msg = ev.msg
        self.print_packet_info(msg.data)

    def print_packet_info(self, data):
        """
        A helper method that prints basic details about common packet types (Ethernet, VLAN, ARP, IPv4, TCP, UDP),
        always showing source and destination ports if available.

        This method is NOT intended to be used. Instead, take bits and pieces from this, and use it for what YOU need.

        As an example - if you need to do if statements on a source/destination ip/port, take the variables used from here! :)
        """
        pkt = packet.Packet(data)

        eth = pkt.get_protocol(ethernet.ethernet)
        if eth:
            self.logger.info("[Ethernet] %s → %s | Ethertype: %s", eth.src, eth.dst, eth.ethertype)

        vlan_pkt = pkt.get_protocol(vlan.vlan)
        if vlan_pkt:
            self.logger.info("[VLAN] ID: %s, Priority: %s", vlan_pkt.vid, vlan_pkt.pcp)

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            self.logger.info("[ARP] %s (%s) → %s (%s) | Opcode: %s",
                             arp_pkt.src_ip, arp_pkt.src_mac, arp_pkt.dst_ip, arp_pkt.dst_mac, arp_pkt.opcode)

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            self.logger.info("[IPv4] %s → %s | Protocol: %s, TOS: %s",
                             ip_pkt.src, ip_pkt.dst, ip_pkt.proto, ip_pkt.tos)

            # Handle transport layer
            src_port = dst_port = None

            if ip_pkt.proto == 6:  # TCP
                tcp_pkt = pkt.get_protocol(tcp.tcp)
                if tcp_pkt:
                    src_port = tcp_pkt.src_port
                    dst_port = tcp_pkt.dst_port
                    self.logger.info("[TCP] Source Port: %s → Destination Port: %s", src_port, dst_port)

            elif ip_pkt.proto == 17:  # UDP
                udp_pkt = pkt.get_protocol(udp.udp)
                if udp_pkt:
                    src_port = udp_pkt.src_port
                    dst_port = udp_pkt.dst_port
                    self.logger.info("[UDP] Source Port: %s → Destination Port: %s", src_port, dst_port)

            else:
                self.logger.info("[Transport] Non-TCP/UDP protocol: %s — no ports to show", ip_pkt.proto)

            # In case src/dst ports still unset
            if src_port is None or dst_port is None:
                self.logger.info("[Ports] No transport-layer ports found in this packet.")
