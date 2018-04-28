"""
Fellyjish Switch (based on POX controller tutorial)
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class FellyjishController(object):

    def __init__ (self, connection):

        self.connection = connection
        connection.addListeners(self)

        # Routing table for switch
        self.mac_to_port = {}


    def resend_packet(self, packet_in, out_port):

        msg = of.ofp_packet_out()
        msg.data = packet_in

        action = of.ofp_action_output(port = out_port)
        msg.actions.append(action)

        self.connection.send(msg)


    def act_like_switch (self, packet, packet_in):

        log.info("Installing flow... src: " + str(packet.src) + " dst: " + str(packet.dst) + " port: " + str(packet_in.in_port))

        msg = of.ofp_flow_mod()
        msg.data = packet_in
        msg.match = of.ofp_match.from_packet(packet)
        
        action = of.ofp_action_output(port = of.OFPP_ALL)
        msg.actions.append(action)

        self.connection.send(msg)


    def _handle_PacketIn (self, event):

        packet = event.parsed
        if not packet.parsed:
          log.warning("Ignoring incomplete packet")
          return

        log.info("Packet with unknown output port received")
        self.act_like_switch(packet, event.ofp)


def launch ():
    """
    Starts the component
    """
    def start_switch (event):
        log.debug("Controlling %s" % (event.connection,))
        FellyjishController(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)

