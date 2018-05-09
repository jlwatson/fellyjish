import argparse
import copy
import networkx as nx
import os
import pickle
import random
import sys

from collections import defaultdict
from subprocess import Popen


RNG_SEED = 0xBAEF


def generate_topology(n_servers, n_switches, n_ports, debug=False):

    if debug:
        random.seed(RNG_SEED)

    sys.stdout.write("Generating Fellyjish topology: %d servers, %d switches, %d ports per switch..." % (n_servers, n_switches, n_ports))

    topo = {}

    G = nx.Graph()
    topo["graph"] = G
    topo["n_ports"] = n_ports

    topo["n_hosts"] = n_servers
    for s in range(n_servers):
        G.add_node('h'+str(s), ip = '10.0.' + str(s) + '.1')

    topo["n_switches"] = n_switches
    outport_mappings = {}
    open_ports = [n_ports] * n_switches 

    for sw in range(n_switches):
        curr_switch = 's'+str(sw)
        G.add_node(curr_switch)

        i = sw
        while i < n_servers:
            G.add_edge('h'+str(i), curr_switch)
            outport_mappings[(curr_switch, 'h'+str(i))] = open_ports[sw]
            outport_mappings[('h'+str(i), curr_switch)] = 1
            i += n_switches
            open_ports[sw] -= 1

    start_open_ports = copy.deepcopy(open_ports)
    
    topo['outport_mappings'] = outport_mappings
    # randomly link the remaining open ports
    links = defaultdict(list)
    while sum(open_ports) > 1:
        open_switches = [x for x in range(n_switches) if open_ports[x] > 0]
        if len(open_switches) == 1: # special case with two ports remaining on same switch
            curr = open_switches[0]
            if open_ports[curr] >= 2:
                other_switches = [s for s in range(n_switches) if s != curr]
                x = 's'+str(random.choice(other_switches))
                y = random.choice(list(nx.all_neighbors(G, x)))
                G.remove_edge(x, y)
                x_port = outport_mappings.pop((x, y))
                y_port = outport_mappings.pop((y, x))
                G.add_edge(x, 's'+str(curr))
                G.add_edge(y, 's'+str(curr))
                outport_mappings[(x, 's'+str(curr))] = x_port
                outport_mappings[('s'+str(curr), x)] = open_ports[curr]
                outport_mappings[(y, 's'+str(curr))] = y_port
                outport_mappings[('s'+str(curr), y)] = open_ports[curr] - 1
                open_ports[curr] -= 2
                continue

        start_over = False
        while True:
            x = random.choice(open_switches)
            x_name = 's'+str(x)
            unconnected_switches = [s for s in open_switches if ('s'+str(s) not in list(G.neighbors(x_name)) and s != x)]
            if len(unconnected_switches) == 0:
                no_new_links = True
                for os in open_switches:
                    for os2 in open_switches:
                        if os != os2:
                            no_new_links = no_new_links and 's'+str(os2) in list(G.neighbors('s'+str(os)))
                if no_new_links:
                    start_over = True
                    break
            else:
                break
        
        if start_over:
            open_ports = copy.deepcopy(start_open_ports)
            G = nx.create_empty_copy(G)
            continue

        y = random.choice(unconnected_switches)
        open_ports[x] -= 1
        open_ports[y] -= 1
        G.add_edge('s'+str(x), 's'+str(y))
        outport_mappings[('s'+str(x), 's'+str(y))] = open_ports[x] + 1
        outport_mappings[('s'+str(y), 's'+str(x))] = open_ports[y] + 1

    sys.stdout.write(" done\n")
    return topo

