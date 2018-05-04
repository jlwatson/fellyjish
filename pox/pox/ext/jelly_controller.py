# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

import pox.lib.packet as pkt

from pox.lib.addresses import IPAddr,EthAddr,parse_cidr
from pox.lib.addresses import IP_BROADCAST, IP_ANY
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.proto.dhcpd import DHCPLease, DHCPD
import pox.proto.arp_responder as arp
from collections import defaultdict
from pox.openflow.discovery import Discovery
import pickle
import time
import networkx as nx

log = core.getLogger()

switches_by_dpid = {}

mac_to_port = {}

algo = 'ecmp'
num_paths = 1

topo = pickle.load(open('/home/diveesh/fellyjish/pox/pox/ext/small_topo.pickle', 'r'))
paths = {}

def k_shortest_paths(G, start, end, k):
    return list(islice(nx.shortest_simple_paths(G, start, end), k))


def ecmp(G, start, end, k):
    paths = []
    for p in nx.shortest_simple_paths(G, start, end):
        if len(paths) < k and (len(paths) == 0 or len(p) == len(paths[0])):
            paths.append(p)
        else:
            break

    return paths

def _get_paths(src, dst):
  if (src, dst) in paths:
    return paths[(src, dst)]
  if algo == 'ecmp':
    fn = ecmp
  else:
    fn = k_shortest_paths

  p_paths = fn(topo['graph'], src, dst, num_paths)
  paths[(src, dst)] = p_paths
  return p_paths

class TopoSwitch (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in, event, srchost, dsthost):
    """
    Implement switch-like behavior.
    """
    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC

    if event.dpid not in mac_to_port:
      mac_to_port[event.dpid] = {}
    mac_to_port[event.dpid][packet.src] = event.port

    this_mac_to_port = mac_to_port[event.dpid]

    packet_paths = _get_paths(srchost, dsthost)
    
    #for now, pick the first path that exists between a pair of endhosts
    path = packet_paths[0]

    if packet.dst in this_mac_to_port:
      # update the routing table to reflect the path this packet needs to take

    else:
      self.resend_packet(packet_in, of.OFPP_ALL)

    """
    if the port associated with the destination MAC of the packet is known:
      # Send packet out the associated port
      self.resend_packet(packet_in, ...)

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(packet_in, of.OFPP_ALL)

    """


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    # log.info("event mac is " + str(event.parsed))
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    #switch mac is event.dpid

    # Comment out the following line and uncomment the one after
    # when starting the exercise.

    log.info("At switch " + str(hex(event.dpid)) + ". Src mac is " + str(packet.src) + ", dest mac is " + str(packet.dst))
    log.info("Coming in at port " + str(event.port))
    log.info("event ip " + str(packet.find('ipv4')))
    log.info(topo['graph'].nodes(data='ip'))

    ipv4 = packet.find('ipv4')
    if ipv4 is not None:
      log.info('src ip is ' + str(ipv4.srcip))
      log.info('dst ip is ' + str(ipv4.dstip))
      srcip = ipv4.srcip
      dstip = ipv4.dstip
      hosts = topo['graph'].nodes(data='ip')
      for host in hosts:
        if host[1] == srcip:
          srchost = host[0]
        if host[1] == dstip:
          dsthost = host[0]
      log.info("src host: " + str(srchost) + ", dsthost: " + str(dsthost))
      self.act_like_switch(packet, packet_in, event, srchost, dsthost)

    # log.info("Src: " + str(packet.src))
    # log.info("Dest: " + str(packet.dst))
    # log.info("Event port: " + str(event.port))
    #self.act_like_hub(packet, packet_in)
    # log.info("packet in")
    



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    #log.info(event.connection[0])
    log.info("Controlling %s" % (event.connection.dpid,))
    sw = switches_by_dpid.get(event.dpid)
    log.info("doin some goooooood stuff")
    if sw is None:
      # New switch
      log.info("in the not found case, dpid is " + str(hex(event.dpid)))
      
      sw = TopoSwitch(event.connection)
      switches_by_dpid[event.dpid] = sw

    else:
      log.info("in the found case, dpid is " + str(event.dpid))

  core.openflow.addListenerByName("ConnectionUp", start_switch)
  arp.launch();

