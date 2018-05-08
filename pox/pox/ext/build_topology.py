import argparse
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

    def build(self, pkl):
        topo = pickle.load(open(pkl, 'r'))
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
            self.mn_switches.append(self.addSwitch('s' + str(s + 1), mac="00:00:00:00:00:" + str("{:02x}".format(s + 1))))

        for e in topo['graph'].edges():
            if e[0][0] == 'h':
                f1 = self.mn_hosts[int(e[0][1:])]
                f1_graph = f1
                switch1 = False
            else:
                f1 = self.mn_switches[int(e[0][1:])]
                f1_graph = 's' + str(int(f1[1:]) - 1)
                switch1 = True 

            if e[1][0] == 'h':
                f2 = self.mn_hosts[int(e[1][1:])]
                f2_graph = f2
                switch2 = False
            else:
                f2 = self.mn_switches[int(e[1][1:])]
                f2_graph = 's' + str(int(f2[1:]) - 1)
                switch2 = True 

            port1 = outport_mappings[(f1_graph, f2_graph)]
            port2 = outport_mappings[(f2_graph, f1_graph)]
            if switch1 and switch2:
                bw = 20
            else:
                bw = 10
            print f1, f2
            self.addLink(f1, f2, bw=5, port1=port1, port2=port2, use_htb=True)

        self.topo = topo


def random_permutation(topo):
    hosts = list(range(topo.topo["n_hosts"])) 
    random.shuffle(hosts)

    pairings = []
    while len(hosts) > 1:
        x, y = hosts[0], hosts[1]

        pairings.append((
            'h'+str(x),
            'h'+str(y)
        ))
        hosts = hosts[2:]

    return pairings


def experiment(net, topo):
    dumpNetConnections(net)
    net.start()
    sleep(3)
    net.pingAll()

    perm = random_permutation(topo)
    for pair in perm:
        host_a = net.getNodeByName(pair[0])
        host_b = net.getNodeByName(pair[1])

        print "Host %s -> Host %s" % (pair[0], pair[1])

        host_a.sendCmd("iperf", "-s", "-t", "20")
        host_b.sendCmd("iperf", "-c", "10.0."+ pair[0][1:] +".1", "-t", "20", "-P", "8")

        output = host_b.waitOutput()
        print output


def main(pkl):

    topo = JellyFishTop(pkl)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX("jelly", cargs2=("--p=%s" % pkl)))

    # set host MAC addresses
    host_mac_base = len(topo.mn_switches)
    for i, h in enumerate(topo.mn_hosts):
        mn_host = net.getNodeByName(h)
        print h, mac_from_value(host_mac_base + i + 1)
        mn_host.setMAC(mac_from_value(host_mac_base + i + 1))
        for j, h2 in enumerate(topo.mn_hosts):
            if i == j: continue
            mn_host2 = net.getNodeByName(h2)
            print "Setting arp for host " + str(h) + ", index " + str(i) + ". j " + str(j) + ", mac is " + mac_from_value(host_mac_base + j + 1)
            mn_host.setARP('10.0.' + str(j) + '.1', mac_from_value(host_mac_base + j + 1))

    experiment(net, topo)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run Jellyfish topology.")
    parser.add_argument('--pickle', help='Topology pickle input path', default=None)
    args = parser.parse_args()

    main(args.pickle)

