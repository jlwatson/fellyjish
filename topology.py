import argparse
import os
import pickle
import random

from collections import defaultdict
from subprocess import Popen

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.node import OVSController
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.util import dumpNetConnections


def generate_topology(n_servers, n_switches, n_ports, debug=False):

    if debug:
        random.seed(0xbeef)

    topo = {} # generated result goes here

    if n_ports < 2:
        raise ValueError("Number of ports per switch must be >= 2")

    if n_switches < n_servers:
        raise ValueError("Number of servers must be greater than or equal to number of hosts (simulated racks)")

    print("Generating fellyjish topology: %d servers, %d switches, %d ports per switch" % (n_servers, n_switches, n_ports))

    hosts = []
    for s in range(n_servers):
        hosts.append('h'+str(s))
    topo["hosts"] = hosts

    switches = []
    open_ports = [n_ports] * n_switches 
    for sw in range(n_switches):
        curr_switch = 's'+str(sw)
        if sw < n_servers: # match switch and paired host
            open_ports[sw] -= 1
        switches.append(curr_switch)
    topo["switches"] = switches

    # randomly link the remaining open ports
    links = defaultdict(list)
    while sum(open_ports) > 1:
        open_switches = [x for x in range(n_switches) if open_ports[x] > 0]
        if len(open_switches) == 1: # special case with two ports remaining on same switch
            curr = open_switches[0]
            if curr >= 2:
                other_switches = [s for s in range(n_switches) if s != curr]
                x = random.choice(other_switches)
                y = random.choice(links[x])
                links[x].remove(y)
                links[y].remove(x)
                links[curr].append(x)
                links[curr].append(y)
                links[x].append(curr)
                links[y].append(curr)
                open_ports[curr] -= 2
                continue

        start_over = False
        while True:
            x = random.choice(open_switches)
            unconnected_switches = [s for s in open_switches if (s not in links[x] and s != x)]
            if len(unconnected_switches) == 0:
                no_new_links = True
                for os in open_switches:
                    for os2 in open_switches:
                        if os != os2:
                            no_new_links = no_new_links and os2 in links[os]
                if no_new_links:
                    start_over = True
                    break
            else:
                break
        
        if start_over:
            open_ports= [n_ports - 1] * n_switches # assume one port only is used for server
            links = defaultdict(list)
            continue

        y = random.choice(unconnected_switches)
        open_ports[x] -= 1
        open_ports[y] -= 1
        links[x].append(y)
        links[y].append(x)

    topo["link_map"] = links

    # generate link pairs and add to network
    link_pairs = set()
    for s1 in links:
        for s2 in links[s1]:
            link_pairs.add((s1, s2) if s1 < s2 else (s2, s1))
    topo["link_pairs"] = link_pairs

    return topo


class JellyFishTop(Topo):

    def build(self, topo_map):
        mn_hosts = []
        for h in topo_map["hosts"]:
            mn_hosts.append(self.addHost(h))

        mn_switches = []
        for i, s in enumerate(topo_map["switches"]):
            switch = self.addSwitch(s)
            mn_switches.append(switch)
            if i < len(topo_map["hosts"]):
                self.addLink(mn_hosts[i], switch)

        for p in topo_map["link_pairs"]:
            self.addLink(mn_switches[p[0]], mn_switches[p[1]])
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Build fellyjish topology.")
    parser.add_argument('--debug', help='run in debug mode (same random seed)', action='store_true')
    parser.add_argument('--pickle', help='Topo pickle file path', default=None)
    args = parser.parse_args()
    
    topo_map = generate_topology(n_servers=3, n_switches=6, n_ports=3, debug=args.debug)
    with open(args.pickle, 'wb') as f:
        pickle.dump(topo_map, f)

    # TODO: move Mininet stuff somewhere else
    # topo = JellyFishTop(topo_map=topo_map)

