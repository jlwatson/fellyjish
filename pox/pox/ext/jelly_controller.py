"""
Fellyjish Switch (based on POX controller tutorial)
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import logging

log = core.getLogger()
log.setLevel(logging.DEBUG)

'''
def handle_link_event(event):
    log.debug("Link event: dpid1,2: %s,%s port1,2: %s, %s" % (event.dpid1, event.dpid2, event.port1, event.port2))
'''

class FellyjishController(object):

    def __init__(self, event):

        self.dpid = event.dpid
        self.connection = event.connection
        self.connection.addListeners(self)

        self.mapping = {}
        # switch_map[self.dpid] = self

    def act_like_switch(self, packet, packet_in):

        print("[%s] Received packet from %s to %s" % (self.connection, packet.src, packet.dst))

        self.mapping[packet.src] = packet_in.in_port
        dst_port = self.mapping.get(packet.dst)
        
        if dst_port is None:
            msg = of.ofp_packet_out()
            msg.data = packet_in
            
            action = of.ofp_action_output(port = of.OFPP_ALL)
            msg.actions.append(action)

            self.connection.send(msg)

        else:
            msg = of.ofp_flow_mod()
            msg.match.dl_dst = packet.src
            msg.match.dl_src = packet.dst
            msg.actions.append(of.ofp_action_output(port = packet_in.in_port))

            self.connection.send(msg)

            msg = of.ofp_flow_mod()
            msg.data = packet_in
            msg.match.dl_dst = packet.dst
            msg.match.dl_src = packet.src
            msg.actions.append(of.ofp_action_output(port = dst_port))

            log.info("[%s] Installing %s (port %s) <--> %s (port %s)" % (self.connection, packet.src, packet_in.in_port, packet.dst, dst_port))
            
            self.connection.send(msg)

    def _handle_PacketIn(self, event):

        packet = event.parsed
        if not packet.parsed:
          log.warning("Ignoring incomplete packet")
          return

        log.debug("Packet with unknown output port received")
        self.act_like_switch(packet, event.ofp)

    '''
    def _handle_LinkEvent(self, event):
        log.debug("Link event: dpid1,2: %s,%s port1,2: %s, %s" % (event.dpid1, event.dpid2, event.port1, event.port2))
        log.debug("own dpid: %s" % self.dpid)
    '''

def launch():

    def start_switch(event):
        FellyjishController(event)

    core.openflow.addListenerByName("ConnectionUp", start_switch)

