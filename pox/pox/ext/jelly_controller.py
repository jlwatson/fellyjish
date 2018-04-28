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


  def act_like_hub (self, packet, packet_in):
    self.resend_packet(packet_in, of.OFPP_ALL)

  def act_like_switch (self, packet, packet_in):

    self.mac_to_port[packet.src] = packet_in.in_port
    if packet.dst in self.mac_to_port:

      self.resend_packet(packet_in, self.mac_to_port[packet.dst]) 

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      '''
      log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      msg = of.ofp_flow_mod()
      
      # Set fields to match received packet
      msg.match = of.ofp_match.from_packet(packet)
      < Set other fields of flow_mod (timeouts? buffer_id?) >
      < Add an output action, and send -- similar to resend_packet() >
      '''
    else:
      # Flood the packet
      self.resend_packet(packet_in, of.OFPP_ALL)


  def _handle_PacketIn (self, event):

    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp

    self.act_like_hub(packet, packet_in)
    log.info("packet in")
    # self.act_like_switch(packet, packet_in)


def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    FellyjishController(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
