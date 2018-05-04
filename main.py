import argparse
import networkx as nx
import pickle
import pprint
import random
import sys
from collections import defaultdict, OrderedDict
from itertools import islice
from time import sleep, time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
from topology import generate_topology


def k_shortest_paths(G, start, end, k):
    return list(islice(nx.shortest_simple_paths(G, start, end), k))


def host_to_switch(topo, h_idx):
    n_switches = topo["n_switches"]
    while h_idx >= n_switches:
        h_idx -= n_switches
    return h_idx


def random_permutation(topo):

    hosts = list(range(topo["n_hosts"])) 
    random.shuffle(hosts)

    pairings = []
    while len(hosts) > 1:
        x, y = hosts[0], hosts[1]
        hosts = hosts[2:]
        pairings.append((
            's'+str(host_to_switch(topo, x)),
            's'+str(host_to_switch(topo, y))
        ))

    return pairings


def is_switch_node(node_name):
    return node_name[0] == 's'


def generate_path_counts(topo, algorithm, k, max_paths_on_link):

    sys.stdout.write("Generating paths using %s (k=%d).." % (algorithm, k))
    sys.stdout.flush()

    while True:
        sys.stdout.write(".")
        sys.stdout.flush()

        switch_pairs = random_permutation(topo)
        paths = []
        for switch1, switch2 in switch_pairs:
            if algorithm == 'k-shortest':
                paths += k_shortest_paths(topo["graph"], switch1, switch2, k)
                paths += k_shortest_paths(topo["graph"], switch2, switch1, k)

        link_paths = {}
        for (u, v) in topo["graph"].edges():
            if is_switch_node(u) and is_switch_node(v):
                link_paths[(u,v)] = 0
                link_paths[(v,u)] = 0

        for p in paths:
            for i in range(len(p)-1):
                link_paths[(p[i], p[i+1])] += 1

        if max(link_paths.values()) <= max_paths_on_link:
            break

    sys.stdout.write(" done\n")
    sys.stdout.flush()
    return link_paths


def generate_figure(cumulative_counts, colors, out_filepath):

    sys.stdout.write("Creating Figure 9...")
    sys.stdout.flush()

    fig = plt.figure()
    ax = fig.add_subplot(111)

    max_length = max([len(c) for c in cumulative_counts])
    
    # TODO: change this for multiple count vectors
    x1 = cumulative_counts[0]
    y1 = range(len(cumulative_counts[0]))

    # TODO: change this for multiple colors
    c1 = colors[0]

    ax.step(x1, y1, linewidth=4, color=c1)  
    plt.title("Jellyfish - Figure 9")
    plt.xlabel("Rank of Link")
    plt.ylabel("# Distinct Paths Link is on")
    plt.xticks(range(0, 3000+1, 500))
    plt.yticks(range(0, max_length+1, 2))
    plt.axis([0, 3003, 0, max_length+0.05])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    plt.grid(linestyle='dotted')
    sys.stdout.write(" done\n")
    sys.stdout.flush()

    sys.stdout.write("Saving figure to %s..." % out_filepath)
    sys.stdout.flush()
    plt.savefig(out_filepath, format="eps", dpi=1000)
    sys.stdout.write(" done\n")
    sys.stdout.flush()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate Jellyfish Figure 9.")
    parser.add_argument('--debug', help='pins RNG and allows debug output', action='store_true')
    parser.add_argument('--pickle', help='Topology pickle output path', default=None)
    parser.add_argument('--servers', help='Number of servers, defaults to 686', default=686, type=int)
    parser.add_argument('--switches', help='Number of switches, defaults to 245', default=245, type=int)
    parser.add_argument('--ports', help='Number of ports per switch, defaults to 14', default=14, type=int)
    parser.add_argument('--figure9', help='Output path for Figure 9 (.eps file), defaults to `figure9.eps`', default='figure9.eps')
    args = parser.parse_args()

    # Generate graph of randomly connected switches
    topo = generate_topology(n_servers=args.servers, n_switches=args.switches, n_ports=args.ports, debug=args.debug)
    if args.pickle:
        with open(args.pickle, 'wb') as f:
            pickle.dump(topo, f)

    # Calculate the random permutation traffic paths across the graph
    link_paths = generate_path_counts(topo, 'k-shortest', 8, 18)
    max_paths = max(link_paths.values())

    # Summarize data for graph
    link_counts = [0] * (max_paths + 1)
    for path_count in link_paths.values():
        link_counts[path_count] += 1

    current_sum = link_counts[0]
    cumulative_link_counts = [current_sum]
    for i in range(1, len(link_counts)):
        current_sum += link_counts[i]
        cumulative_link_counts.append(current_sum)

    # Generate Figure 9
    generate_figure([cumulative_link_counts], [(0.204, 0.216, 0.592)], args.figure9)

    print
    print "Reproduction script completed successfully"

