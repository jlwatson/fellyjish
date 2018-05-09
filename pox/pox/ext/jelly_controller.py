from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.proto.arp_responder as arp
import pickle
import time
import networkx as nx
from itertools import islice
import pox.openflow.spanning_tree as st
from pox.lib.addresses import IPAddr


log = core.getLogger()
paths = {}
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


class TopoSwitch (object):

  def __init__ (self, connection, dpid, t, algo):
    self.connection = connection
    self.name = 's' + str(int(dpid))
    self.graph_name = 's' + str(int(dpid) - 1)

    self.TOPO = t
    self.algo = algo
    self.num_paths = 8

    connection.addListeners(self)


  def _get_paths(self, src, dst):
    if (src, dst) in paths:
      return paths[(src, dst)]
    if self.algo == 'ecmp':
      fn = ecmp
    else:
      fn = k_shortest_paths

    p_paths = fn(self.TOPO['graph'], src, dst, self.num_paths)
    paths[(src, dst)] = p_paths
    return p_paths


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
    packet_paths = self._get_paths(srchost, dsthost)
    path = packet_paths[packet_id % len(packet_paths)]
    next_host_index = path.index(self.graph_name) + 1

    outport = self.TOPO['outport_mappings'][(self.graph_name, path[next_host_index])]
    log.info("Sending packet " + str(packet_id) + " from " + self.graph_name + " to " + str(path[next_host_index]) + " on port " + str(outport))
    self.resend_packet(packet_in, outport)
    return outport

    

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
    log.info(self.TOPO['graph'].nodes(data='ip'))

    tcpp = packet.find('tcp')
    if tcpp is not None:
      log.info(tcpp)
      log.info("ALRIGHT OKAY OKAY ALRIGHT")
      msg = of.ofp_flow_mod()
      msg.priority = 42
      msg.match.dl_type = 0x800
      msg.match.nw_proto = 6
      msg.match.tp_src = tcpp.srcport #get src port
      ipv4 = packet.find('ipv4')
      if ipv4 is not None: #should not be none, cuz if its TCP, it has to be IP as well
        srcip = ipv4.srcip
        dstip = ipv4.dstip
        msg.match.nw_src = IPAddr(ipv4.srcip)
        msg.match.nw_dst = IPAddr(ipv4.dstip)
        hosts = self.TOPO['graph'].nodes(data='ip')
        for host in hosts:
          if host[1] == srcip:
            srchost = host[0]
          if host[1] == dstip:
            dsthost = host[0]
        outport = self.act_like_switch(packet, packet_in, event, srchost, dsthost, tcpp.srcport)
        msg.actions.append(of.ofp_action_output(port = outport))
        self.connection.send(msg)
      # 
    else:
      ipv4 = packet.find('ipv4')
      if ipv4 is not None:
        log.info("just the ping case")
        srcip = ipv4.srcip
        dstip = ipv4.dstip
        hosts = self.TOPO['graph'].nodes(data='ip')
        for host in hosts:
          if host[1] == srcip:
            srchost = host[0]
          if host[1] == dstip:
            dsthost = host[0]
        log.info("src host: " + str(srchost) + ", dsthost: " + str(dsthost))
        self.act_like_switch(packet, packet_in, event, srchost, dsthost, ipv4.id)


def launch(p, algo):

  log.info("pickle path: " + p)
  t = pickle.load(open(p, 'r'))

  log.info("routing algorithm used: " + algo)

  def start_switch (event):
    log.info("Controlling %s" % (event.connection,))
    log.info("DPID is "  + str(event.dpid))
    TopoSwitch(event.connection, event.dpid, t, algo)

  core.openflow.addListenerByName("ConnectionUp", start_switch)

