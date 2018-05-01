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


class JellyFishTop(Topo):

    def build(self, nServers, nSwitches, nPorts):

        if nPorts < 2:
            raise ValueError("Number of ports per switch must be >= 2")

        if nSwitches < nServers:
            raise ValueError("Number of servers must be greater than or equal to number of hosts (simulated racks)")

        print("Creating topology: %d servers, %d switches, %d ports per switch" % (nServers, nSwitches, nPorts))

        hosts = []
        for s in range(nServers):
            hosts.append(self.addHost('h'+str(s), mac='00:00:00:00:00:0'+str(s)))

        switches = []
        openPorts = [nPorts] * nSwitches 
        for sw in range(nSwitches):
            currSwitch = self.addSwitch('s'+str(sw))
            if sw < nServers: # match switch and paired host
                self.addLink(hosts[sw], currSwitch)
                openPorts[sw] -= 1
            switches.append(currSwitch)

        # randomly link the remaining open ports
        links = defaultdict(list)
        while sum(openPorts) > 1:
            openSwitches = [x for x in range(nSwitches) if openPorts[x] > 0]

            if len(openSwitches) == 1: # special case with two ports remaining on same switch
                curr = openSwitches[0]
                otherSwitches = [s for s in range(nSwitches) if s != curr]
                x = random.choice(otherSwitches)
                y = random.choice(links[x])

                links[x].remove(y)
                links[y].remove(x)
                links[curr].append(x)
                links[curr].append(y)
                links[x].append(curr)
                links[y].append(curr)
                
                openPorts[curr] -= 2
                continue

            x = random.choice(openSwitches)
            unconnectedSwitches = [s for s in openSwitches if (s not in links[x] and s != x)]
            y = random.choice(unconnectedSwitches)
            openPorts[x] -= 1
            openPorts[y] -= 1
            links[x].append(y)
            links[y].append(x)

        # generate link pairs and add to network
        link_pairs = set()
        for s1 in links:
            for s2 in links[s1]:
                link_pairs.add((s1, s2) if s1 < s2 else (s2, s1))

        # XXX: for now, remove cycles in graph
        link_pairs.remove((1, 5))
        link_pairs.remove((2, 5))

        for p in link_pairs:
            self.addLink(switches[p[0]], switches[p[1]])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Build fellyjish topology.")
    parser.add_argument('--debug', help='run in debug mode (same random seed)', action='store_true')
    parser.add_argument('--pickle', help='Topo pickle file path', default='topo.pickle')
    args = parser.parse_args()
    
    if args.debug:
        random.seed(0xbeef)

    topo = JellyFishTop(nServers=3, nSwitches=6, nPorts=3)
    with open(args.pickle, 'wb') as f:
        pickle.dump(topo, f)

