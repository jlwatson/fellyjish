import os
import sys
import random
from collections import defaultdict
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time

from mininet.util import dumpNodeConnections, dumpNetConnections

import pickle


def mac_from_value(v):
    return ':'.join(s.encode('hex') for s in ('%0.12x' % v).decode('hex'))


class JellyFishTop(Topo):

    def build(self):
        topo = pickle.load(open('small_topo.pickle', 'r'))
        outport_mappings = topo['outport_mappings']
        print outport_mappings
        self.mn_hosts = []
        for h in range(topo['n_hosts']):
            hosts_from_graph = topo['graph'].nodes(data='ip')
            for host in hosts_from_graph:
                if host[0] == 'h' + str(h):
                    break
            print host
            self.mn_hosts.append(self.addHost('h' + str(h), ip=host[1]))

        self.mn_switches = []
        for s in range(topo['n_switches']):
            print "00:00:00:00:11:" + str("{:02x}".format(s))
            self.mn_switches.append(self.addSwitch('s' + str(s), mac="00:00:00:00:11:" + str("{:02x}".format(s))))

        for e in topo['graph'].edges():
            print e
            if e[0][0] == 'h':
                f1 = self.mn_hosts[int(e[0][1:])]
            else:
                f1 = self.mn_switches[int(e[0][1:])]

            if e[1][0] == 'h':
                f2 = self.mn_hosts[int(e[1][1:])]
            else:
                f2 = self.mn_switches[int(e[1][1:])]

            port1 = outport_mappings[(f1, f2)]
            port2 = outport_mappings[(f2, f1)]
            self.addLink(f1, f2, port1=port1, port2=port2)


def experiment(net, topo):
    dumpNetConnections(net)
    net.start()
    sleep(3)
    net.pingAll()
    # net.pingFull(hosts=net.hosts)
    net.stop()

def main():
    topo = JellyFishTop()
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)

    # set host MAC addresses
    host_mac_base = len(topo.mn_switches)
    for i, h in enumerate(topo.mn_hosts):
        mn_host = net.getNodeByName(h)
        print h, mac_from_value(host_mac_base + i + 1)
        mn_host.setMAC(mac_from_value(host_mac_base + i + 1))

    experiment(net, topo)

if __name__ == "__main__":
    main()

