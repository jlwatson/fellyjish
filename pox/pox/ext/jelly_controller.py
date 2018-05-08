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
import pox.proto.arp_responder as arp
import pickle
import time
import networkx as nx
from itertools import islice
import pox.openflow.spanning_tree as st

topo = pickle.load(open('/home/diveesh/fellyjish/pox/pox/ext/small_topo.pickle', 'r'))

log = core.getLogger()
paths = {}
algo = 'ecmp'
num_paths = 8
switches_by_dpid = {}

def ipinfo (ip):
  parts = [int(x) for x in str(ip).split('.')]
  ID = parts[1]
  port = parts[2]
  num = parts[3]
  return switches_by_id.get(ID),port,num

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
  def __init__ (self, connection, dpid):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection
    self.name = 's' + str(int(dpid))
    self.graph_name = 's' + str(int(dpid) - 1)

    # This binds our PacketIn event listener
    connection.addListeners(self)
    #core.ARPHelper.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  # def _handle_ARPRequest (self, event):
  #   if ipinfo(event.ip)[0] is not self: return
  #   event.reply = self.mac

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


  def act_like_switch (self, packet, packet_in, event, srchost, dsthost, packet_id):
    packet_paths = _get_paths(srchost, dsthost)
    path = packet_paths[packet_id % num_paths]
    next_host_index = path.index(self.graph_name) + 1

    outport = topo['outport_mappings'][(self.graph_name, path[next_host_index])]
    log.info("Sending packet " + str(packet_id) + " from " + self.graph_name + " to " + str(path[next_host_index]) + " on port " + str(outport))
    self.resend_packet(packet_in, outport)

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    log.info("makin some moves big d")
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    log.info("At switch " + str(hex(event.dpid)) + ". Src mac is " + str(packet.src) + ", dest mac is " + str(packet.dst))
    log.info("Coming in at port " + str(event.port))
    log.info("event ip " + str(packet.find('ipv4')))
    log.info(topo['graph'].nodes(data='ip'))

    ipv4 = packet.find('ipv4')
    if ipv4 is not None:
      log.info('src ip is ' + str(ipv4.srcip))
      log.info('dst ip is ' + str(ipv4.dstip))
      log.info('packet id is ' + str(ipv4.id))
      srcip = ipv4.srcip
      dstip = ipv4.dstip
      hosts = topo['graph'].nodes(data='ip')
      for host in hosts:
        if host[1] == srcip:
          srchost = host[0]
        if host[1] == dstip:
          dsthost = host[0]
      log.info("src host: " + str(srchost) + ", dsthost: " + str(dsthost))
      self.act_like_switch(packet, packet_in, event, srchost, dsthost, ipv4.id)

    # arp_info = packet.find('arp')
    # if arp is not None:
    #   log.info('arp packet i guess')

    #self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.info("Controlling %s" % (event.connection,))
    log.info("DPID is "  + str(event.dpid))
    TopoSwitch(event.connection, event.dpid)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
