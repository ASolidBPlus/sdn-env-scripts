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
        self.preferred_port = 1


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Method called when Switch first connects to the Ryu Controller. Used to add initial flow tables.
        """

        self.logger.info("Switch connected... loading flows....")

        # Add appropriate tutorial methods here



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handles packets sent to the controller and prints basic info.
        """
        msg = ev.msg
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)  # Parse the raw packet data
        switch_id = datapath.id

        # Print the raw packet for basic visibility
        self.logger.info(f"Packet received from switch {switch_id}...")

        # Add appropriate tutorial methods here

    def tutorial_match_arp_and_icmp_normal(self, ev):
        """
        Custom method used to showcase matching of ICMP + ARP, and applying the "NORMAL" and OUTPUT: CONTROLLER methods
        """

        # First, lets create the datapath object
        datapath = ev.msg.datapath

        # Then, you want to create your parser and ofproto objects
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Lets make our first match - lets match ARP packets
        # To do this, we will make use of the OFPMatch class using our 'parser' object, and make user of the 'arp' ether_type
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP)

        # Now, lets make our actions. We will do a "NORMAL" action, which effectively makes a switch act in its normal state.
        # We will also do an OUTPUT to CONTROLLER, so we can have overseeing vision on everything.
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_NORMAL),
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)
        ]

        # We will now install that flow into the table
        self.install_flow(datapath, 0, match, actions) # The zero is the priority - the higher the number the higher weighted. Remember, only one flow can be matched at a given time.

        # But wait, this didn't cover ICMP!
        # You can only match one specific thing at a time.
        # If you want to match something else, you need a new flow@
        # Lets make an ICMP match

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=1) # ip_proto '1' = ICMP

        # Remember, we don't need to recreate the actions variable again, as it will keep the same actions!
        self.install_flow(datapath, 0, match, actions) # The zero is the priority - the higher the number the higher weighted. Remember, only one flow can be matched at a given time.

    
    def tutorial_packet_manipulation_flow(self, ev):
        """
        Custom method to showcase packet manipulation when a UDP packet destined for port 4000 is sent. This method will modify the packet to be destined to 400, as well as modifying the IP + MAC Sources.
        """
        
        datapath = ev.msg.datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Let's make a flow that manipulates the packet just a tiny bit!
        # Let's make it so that it detects all UDP Traffic going to port 4000, and change it to 400!
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=inet.IPPROTO_UDP, udp_dst=4000)

        # Now, let's make a few modifications to ports with this destination!
        # We'll modify the UDP Port, as well as the source IP Address!
        # We'll finally allow it so it handles traffic normally, otherwise!

        actions = [
            parser.OFPActionSetField(udp_dst=400), # Sets Destination Port
            parser.OFPActionSetField(ipv4_src='255.255.255.255'), # Sets Source IPv4
            parser.OFPActionSetField(eth_src='ff:ff:ff:ff:ff:ff'), # Sets Source MAC Address
            parser.OFPActionOutput(ofproto.OFPP_NORMAL) # Normal Output
        ]

        # Now, let's install the flow using our premade install_flow method!
        self.install_flow(datapath, 1, match, actions)

        # We need to handle normal traffic, too. Lets do a basic match that matches everything, and then have an action for the Normal Output.
        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(ofproto.OFPP_NORMAL)
        ]

        # Let's again install the flow, but lets make it a lower priority so it does not get matched before our Destination Port flow entry!
        self.install_flow(datapath, 0, match, actions)

    def tutorial_advanced_sdn_manipulation(self, ev):
        """
        Advanced level SDN Manipulation, to show the extent of how network devices can be used to make programmable networks. This uses network concepts like "VLAN's" slightly differently, as a way to 'prioritise' certain traffic.
        We're going to create a topology that looks like this:

        A custom topology is used for this, see here:

        [h1] --> [Leaf Switch 1] -->  [Spine Switch]
                                    /               \
                            Fast Lane (No Delay)      Slow Lane (With Delay)
                                    \               /
                                    [Leaf Switch 2]
                                    /               \
                                [h2]            [h3]

        This mininet topology is found in week_13_advanced_sdn_manipulation_topology.py

        To make this work, we will also be showcasing the usage of packet in alongside of this. This is NOT a requirement to set it up, it's just used as an example.

        """

        datapath = ev.msg.datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        self.logger.info(datapath.id)

        # We have three different types of switches here with different flows, we need a different approach to instlaling flows. We will use if statements based on their DPID.
        # We have preset the DPID's as per the following: Leaf Switch = 1, Spine Switch = 2, Leaf Switch 2 = 3

        if datapath.id == 1:
            self.logger.info("Leaf Switch 1 connected")

            # For Leaf Switch 1, we are going to be forwarding everything to the controller to deal with.
            # This is to showcase Packet In functionality, it is not a requirement for what we're going to pull off.

            # Match everything
            match = parser.OFPMatch()

            # Send to controller
            actions = [
                parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)
            ]
            
            # We will now install the flow
            self.install_flow(datapath, 0, match, actions)

        elif datapath.id == 2:
            self.logger.info("Spine Switch connected")

            # We are going to make a match for VLAN traffic. Dependent on what vlan (100 or 200), it will send it towards different ports.
            # One port will have a delay, the other will not.

            match = parser.OFPMatch(
                vlan_vid=(100 | 0x1000 ) # Matching VLAN 100
            )
            
            # We will now set the actions to remove the VLAN (as they have served their process), and forward to the optimal port (2).
            actions = [
                parser.OFPActionPopVlan(), # Removes VLAN Header
                parser.OFPActionOutput(2)  # Sends out to Port 2
            ]

            self.install_flow(datapath, 1, match, actions)

            # We now need to do for VLAN 200! It will be slightly different.

            match = parser.OFPMatch(
                vlan_vid=(200 | 0x1000 ) # Matching VLAN 100
            )

            actions = [
                parser.OFPActionPopVlan(), # Removes VLAN Header
                parser.OFPActionOutput(3)  # Sends out to Port 2
            ]

            self.install_flow(datapath, 1, match, actions)

            # We also have to add a basic flow that matches everything else and does normal output.
            
            match = parser.OFPMatch() # Matches everything

            actions = [
                parser.OFPActionOutput(ofproto.OFPP_NORMAL)
            ]

            self.install_flow(datapath, 0, match, actions)

        elif datapath.id == 3:
            self.logger.info("Leaf Switch 2 Connected")

            # Due to the way we've set this up, we could actually create a Broadcast Storm if we're not careful!
            # If we did an OFPP_NORMAL, the packet received on Leaf Switch 2 would flood to the alternative port to Spine Switch.
            # In a real world environment, this is why we have STP :)
            # We're going to statically set what ports the IP's are for to prevent the broadcast storm.

            # Let's do this first for 10.0.0.2 Packets

            # First the IP rule
            match_ip = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, # IPv4
            ipv4_dst='10.0.0.2'               # Destination IP
        )

            match_arp = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_ARP,           # ARP
                arp_tpa='10.0.0.2'                           # ARP Target Protocol Address (destination IP)
            )

            actions = [parser.OFPActionOutput(3)]
            self.install_flow(datapath, priority=1, match=match_ip, actions=actions)
            self.install_flow(datapath, priority=1, match=match_arp, actions=actions)

            # Now lets do the same for 10.0.0.3
            match_ip = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, # IPv4
            ipv4_dst='10.0.0.3'               # Destination IP
        )

            match_arp = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_ARP,           # ARP
                arp_tpa='10.0.0.3'                           # ARP Target Protocol Address (destination IP)
            )

            actions = [parser.OFPActionOutput(4)]
            self.install_flow(datapath, priority=1, match=match_ip, actions=actions)
            self.install_flow(datapath, priority=1, match=match_arp, actions=actions)

            # And the same for 10.0.0.1

            match_ip = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, # IPv4
            ipv4_dst='10.0.0.1'               # Destination IP
        )

            match_arp = parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_ARP,           # ARP
                arp_tpa='10.0.0.1'                           # ARP Target Protocol Address (destination IP)
            )

            actions = [parser.OFPActionOutput(2)]
            self.install_flow(datapath, priority=1, match=match_ip, actions=actions)
            self.install_flow(datapath, priority=1, match=match_arp, actions=actions)

    def tutorial_advanced_sdn_manipulation_packet_in(self, ev):
        """
        The Packet In portion of the advanced sdn manipulation tutorial.

        This needs to be used inside packet_in_handler.

        This will dependent on the destination it is headed, tag the device with either VLAN 100 (low priority) or VLAN 200 (high priority)
        """
        datapath = ev.msg.datapath

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # First, we need to parse the packet that has come through, and be able to read it.
        pkt = packet.Packet(ev.msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)  # Ethernet layer
        ip_pkt = pkt.get_protocol(ipv4.ipv4)  # IPv4 layer
        arp_pkt = pkt.get_protocol(arp.arp)   # ARP Layer

        # Now, we're going to be checking if the destination IP Address is to either of our targets. If it is, we will be applying a VLAN tag.
        # We will check both for ARP Requests, as well as general IP Requests.

        vlan_id = None
        if ip_pkt:
            self.logger.info("IP Packet found")
            if ip_pkt.dst == '10.0.0.2':
                vlan_id = 100
            elif ip_pkt.dst == '10.0.0.3':
                vlan_id = 200
        elif arp_pkt:
            self.logger.info("Arp Packet Found")
            if arp_pkt.dst_ip == '10.0.0.2':
                vlan_id = 100
            elif arp_pkt.dst_ip == '10.0.0.3':
                vlan_id = 200
        
        
        # Now, lets begin to make our actions
        # We're going to apply the VLAN_ID and force it to the Spine Switch if a VLAN_ID is detected.
        if vlan_id:
            self.logger.info(f"Setting VLAN {vlan_id}")
            actions = [
            parser.OFPActionPushVlan(ether_types.ETH_TYPE_8021Q), # This creates a VLAN Header, 8021Q = VLAN Header
            parser.OFPActionSetField(vlan_vid=(vlan_id | 0x1000)), # Sets the VLAN ID
            parser.OFPActionOutput(2) # We are specifying to send it out of Port 2, which is the port that is connected to the Spine Leaf
            ]

        else:
            actions = [
                parser.OFPActionOutput(ofproto.OFPP_NORMAL) # Just normal switch output if no VLAN created, this will allow for traffic coming back from H2/H3
            ]

        self.send_packet_out(ev, actions)



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

    def send_packet_out(self, ev, actions):
        """
        Sends a packet out. Used when you have modified a packet for during a PacketIn event.
        """
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ev.msg.buffer_id,
            in_port=ev.msg.match['in_port'],
            actions=actions,
            data=ev.msg.data
        )

        datapath.send_msg(out)

