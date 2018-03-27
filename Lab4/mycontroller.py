from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        # arp table: for searching
        self.arp_table={}
        self.arp_table['10.0.0.1'] = '00:00:00:00:00:01'
        self.arp_table['10.0.0.2'] = '00:00:00:00:00:02'
        self.arp_table['10.0.0.3'] = '00:00:00:00:00:03'
        self.arp_table['10.0.0.4'] = '00:00:00:00:00:04'
    """
        Hand-shake event call back method
        This is the very initial method where the switch hand shake with the controller
        It checks whether both are using the same protocol version: OpenFlow 1.3 in this case

        Therefore in this method, setup some static rules.
        e.g. the rules which sends unknown packets to the controller
             the rules directing TCP/UDP/ICMP traffic
             ACL rules
    """
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Insert Static rule
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Installing static rules to process TCP/UDP and ICMP and ACL
        dpid = datapath.id  # classifying the switch ID
        if dpid == 1: # switch S1
            ### self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.1', 10, 1)
            #10.0.0.1 is dst ip address, 1 is switch port number
            # for switch 1, what port number should choose to forward that dst address
            ### implement tcp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 2)
            ### implement icmp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 2)
            ### implement udp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.3', 20, 3)
            ### implement udp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.2', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 3)

            ### implement ACL
            ### drop UDP from 10.0.0.1 to 10.0.0.4 without notification
            match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,
                                    ipv4_src = '10.0.0.1',
                                    ipv4_dst = '10.0.0.4',
                                    ip_proto = inet.IPPROTO_UDP)
            actions = []
            self.add_flow(datapath, 20, match, actions)  #add a flow to controller

        elif dpid == 2: # switch S2
            ### implement tcp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 3)
            ### implement tcp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.4', 20, 3)

            ### implement icmp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 3)
            ### implement icmp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.4', 10, 3)

            ### implement udp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.2', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 1)

            # implement ACL rules
            # this rule directs the TCP packets from h2 to h4 to the controller
            match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,
                                    ipv4_src = '10.0.0.2',
                                    ipv4_dst = '10.0.0.4',
                                    ip_proto = inet.IPPROTO_TCP,
                                    tcp_src = 80)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 30, match, actions)


        elif dpid == 3: # switch S3
            # fwding everthing between port 1 and port 2

            ### implement tcp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 3)
            ### implement tcp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.4', 20, 2)

            ### implement icmp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 3)
            ### implement icmp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.4', 10, 2)

            ### implement udp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.3', 20, 3)

        elif dpid == 4: # switch S4
            ### implement tcp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.2', 20, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.3', 20, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_TCP, '10.0.0.4', 20, 2)
            ### implement icmp fwding
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.3', 10, 3)
            self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.4', 10, 2)
            ### implement udp fwding1
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 2)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.3', 20, 3)
            ### implement udp fwding2
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.2', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.1', 20, 1)
            self.add_layer4_rules(datapath, inet.IPPROTO_UDP, '10.0.0.4', 20, 2)
            
            # implement ACL rules
            # this rule directs the TCP packets from h4 to h2 to the controller
            match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,
                                    ipv4_src = '10.0.0.4',
                                    ipv4_dst = '10.0.0.2',
                                    ip_proto = inet.IPPROTO_TCP,
                                    tcp_src = 80)
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 30, match, actions)


            ### implement ACL
            ### drop UDP from 10.0.0.4 to 10.0.0.1 without notification
            match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,
                                    ipv4_src = '10.0.0.4',
                                    ipv4_dst = '10.0.0.1',
                                    ip_proto = inet.IPPROTO_UDP)
            actions = []
            self.add_flow(datapath, 20, match, actions)

        else:
            print "wrong switch"


    """
        Call back method for PacketIn Message
        This is the call back method when a PacketIn Msg is sent
        from a switch to the controller
        It handles L3 classification in this function:
    """
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ethertype = eth.ethertype

        # process ARP
        if ethertype == ether.ETH_TYPE_ARP:
            self.handle_arp(datapath, in_port, pkt)
            return

        # process IP
        if ethertype == ether.ETH_TYPE_IP:
            self.handle_ip(datapath, in_port, pkt)
            return

    # Member methods you can call to install TCP/UDP/ICMP fwding rules
    def add_layer4_rules(self, datapath, ip_proto, ipv4_dst = None, priority = 1, fwd_port = None):
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(fwd_port)]
        match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,
                                ip_proto = ip_proto,
                                ipv4_dst = ipv4_dst)
        self.add_flow(datapath, priority, match, actions)

    # Member methods you can call to install general rules
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    """
        Methods to handle ARP.
    """

    def handle_arp(self,datapath,in_port,pkt): 
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    eth_pkt = pkt.get_protocol(ethernet.ethernet) 
    arp_pkt = pkt.get_protocol(arp.arp)         
    arp_resolv_mac = self.arp_table[arp_pkt.dst_ip]

    new_packet = packet.Packet() 
    new_packet.add_protocol(ethernet.ethernet(ethertype=eth_pkt.ethertype, dst=eth_pkt.src, src=arp_resolv_mac))

    new_packet.add_protocol(arp.arp(opcode=arp.ARP_REPLY, src_mac=arp_resolv_mac, src_ip=arp_pkt.dst_ip, dst_mac=arp_pkt.src_mac, dst_ip=arp_pkt.src_ip))

    new_packet.serialize()
    actions = [parser.OFPActionOutput(in_port)] 
    out = parser.OFPPacketOut(datapath,

    ofproto.OFP_NO_BUFFER, ofproto.OFPP_CONTROLLER,

    actions, new_packet.data)

    datapath.send_msg(out) 

    
    def handle_ip(self, datapath, in_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        ipv4_pkt = pkt.get_protocol(ipv4.ipv4) # parse out the IPv4 pkt

        if datapath.id == 1 and ipv4_pkt.proto == inet.IPPROTO_TCP:
            tcp_pkt = ipv4_pkt.get_protocol(tcp.tcp) # parser out the TCP pkt

            ### generate the TCP packet with the RST flag set to 1
            ### packet generation is similar to ARP,
            ### but you need to generate ethernet->ip->tcp and serialize it
            eth_pkt = ipv4_dst.get_protocol(ethernet, ethernet)
            tcp_hd = tcp.tcp(ack = tcp_pkt.seq + 1, src_port = tcp_pkt.dst_port, dst_port = tcp_pkt.src_port, bits = 20)
            ip_hd = ipv4.ipv4(dst = ipv4_pkt.src, src = ipv4_pkt.dst, proto = ipv4_pkt.proto)
            ether_hd = ethernet.ethernet(ethertype = ether.ETH_TYPE_IP, dst = eth_pkt.src, src = eth_pkt.dst)
            tcp_rst_ack = packet.Packet()
            tcp_rst_ack.add_protocol(ether_hd)
            tcp_rst_ack.add_protocol(ip_hd)
            tcp_rst_ack.add_protocol(tcp_hd)
            tcp_rst_ack.serialize()
        # send the Packet Out mst to back to the host who is initilaizing the ARP
            actions = [parser.OFPActionOutput(in_port)];
            out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER,
                                      ofproto.OFPP_CONTROLLER, actions,
                                      tcp_rst_ack.data)
            datapath.send_msg(out)