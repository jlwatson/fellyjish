import argparse
import os
import random
import sys

from collections import defaultdict
from subprocess import Popen
from time import sleep, time

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.node import OVSController
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.util import dumpNetConnections

sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX


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
            # print openSwitches
            if len(openSwitches) == 1: # special case with two ports remaining on same switch
                curr = openSwitches[0]
                if curr >= 2:
                    otherSwitches = [s for s in range(nSwitches) if s != curr]
                    x = random.choice(otherSwitches)
                    y = random.choice(links[x])
                    print 'HITME~~!~!~!~'
                    links[x].remove(y)
                    links[y].remove(x)
                    links[curr].append(x)
                    links[curr].append(y)
                    links[x].append(curr)
                    links[y].append(curr)
                    openPorts[curr] -= 2
                    continue

            startOver = False
            while True:
                x = random.choice(openSwitches)
                unconnectedSwitches = [s for s in openSwitches if (s not in links[x] and s != x)]
                if len(unconnectedSwitches) == 0:
                    noNewLinks = True
                    for os in openSwitches:
                        for os2 in openSwitches:
                            if os != os2:
                                noNewLinks = noNewLinks and os2 in links[os]
                    if noNewLinks:
                        startOver = True
                        break
                else:
                    break
            
            if startOver:
                openPorts = [nPorts - 1] * nSwitches # assume one port only is used for server
                links = defaultdict(list)
                continue

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
        # link_pairs.remove((1, 5))
        # link_pairs.remove((2, 5))

        for p in link_pairs:
            self.addLink(switches[p[0]], switches[p[1]])


def experiment(net):
    net.start()
    dumpNetConnections(net)
    sleep(3)
    net.ping(net.hosts[:2])
    net.stop()


def main(debug):

    if debug:
        random.seed(0xbeef)

    topo = JellyFishTop(nServers=50, nSwitches=50, nPorts=5)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    experiment(net)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run fellyjish experiment.")
    parser.add_argument('--debug', help='run in debug mode (same random seed)', action='store_true')
    args = parser.parse_args()

    main(args.debug)

