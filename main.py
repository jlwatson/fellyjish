import argparse
import networkx as nx
import os
import pickle
import random
import re
import subprocess
import sys
from collections import defaultdict, OrderedDict
from itertools import islice
from time import sleep, time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 

from topology import generate_topology

sys.path.append("./pox/")
from pox.ext.build_topology import build_and_run


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

        x_switch = host_to_switch(topo, x)
        y_switch = host_to_switch(topo, y)

        # if x and y are at the same switch, reshuffle remaining hosts and retry
        if x_switch == y_switch:
            random.shuffle(hosts)
            continue

        pairings.append((
            's'+str(x_switch),
            's'+str(y_switch)
        ))
        hosts = hosts[2:]

    return pairings


def is_switch_node(node_name):
    return node_name[0] == 's'


def generate_path_counts(topo, algorithm, k, target_paths_on_link):
    sys.stdout.write("Generating paths using %s (k=%d).." % (algorithm, k))
    sys.stdout.flush()

    while True:
        sys.stdout.write(".")
        sys.stdout.flush()

        switch_pairs = random_permutation(topo)
        paths = []
        for switch1, switch2 in switch_pairs:
            if algorithm == 'k-shortest':
                fn = k_shortest_paths
            else: # algorithm == 'ecmp':
                fn = ecmp

            paths += fn(topo["graph"], switch1, switch2, k)
            paths += fn(topo["graph"], switch2, switch1, k)

        link_paths = {}
        for (u, v) in topo["graph"].edges():
            if is_switch_node(u) and is_switch_node(v):
                link_paths[(u,v)] = 0
                link_paths[(v,u)] = 0

        for p in paths:
            for i in range(len(p)-1):
                link_paths[(p[i], p[i+1])] += 1

        if max(link_paths.values()) == target_paths_on_link:
            break

    sys.stdout.write(" done\n")
    sys.stdout.flush()
    return link_paths


def summarize(link_paths):
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

    return cumulative_link_counts


def generate_figure(cumulative_counts, format_options, out_filepath):

    sys.stdout.write("Creating Figure 9...")
    sys.stdout.flush()

    fig = plt.figure()
    ax = fig.add_subplot(111)

    max_length = max([len(c) for c in cumulative_counts])
    
    x = cumulative_counts
    y = [range(len(cc)) for cc in cumulative_counts]

    for i in range(len(cumulative_counts)):
        ax.step(x[i], y[i], **format_options[i])

    plt.title("Jellyfish - Figure 9")
    plt.xlabel("Rank of Link")
    plt.ylabel("# Distinct Paths Link is on")
    plt.xticks(range(0, 3000+1, 500))
    plt.yticks(range(0, max_length+1, 2))
    plt.axis([0, 3003, 0, max_length])
    plt.legend(loc=2)
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


def cleanmn():
    sys.stdout.write("Cleaning Mininet...")
    sys.stdout.flush()
    FNULL = open(os.devnull, 'w')
    subprocess.call(["sudo", "mn" , "-c"], stdout=FNULL, stderr=subprocess.STDOUT)
    sys.stdout.write(" done\n")
    sys.stdout.flush()


def run_table_test(cwd, topology, algo, flows):

    cleanmn()

    sys.stdout.write("Testing throughput values for algorithm `%s` with TCP %d flows..." % (algo, flows))
    sys.stdout.flush()

    os.chdir(os.path.join(cwd, 'pox/pox/ext'))
    subprocess.call(["sudo", "python", "build_topology.py", "--pickle", topology, "--algo", algo, "--nflows", str(flows), "--output", "test_output.pickle"])
    with open("test_output.pickle", 'rb') as f:
        output = pickle.load(f)
    os.chdir(cwd)

    sys.stdout.write(" done\n")
    sys.stdout.flush()

    return output


HOST_LINK_BW = 5.0

def parse_one_flow_output(result):
    out = result["output"]

    bandwidth_values = []
    for hostpair_out in out:
        summary = hostpair_out[-2] 
        # assume Mbits/sec
        bandwidth_values.append(float(re.search('(\d+.\d+) .bits\/sec$', summary).group(1))) 

    avg_bw = sum(bandwidth_values) / len(bandwidth_values) 
    return (avg_bw / HOST_LINK_BW) * 100

def parse_multi_flow_output(result):
    out = result["output"]

    summed_bandwidth_values = []
    for hostpair_out in out:
        summary = hostpair_out[-2] 
        # assume Mbits/sec
        summed_bandwidth_values.append(float(re.search('(\d+.\d+) .bits\/sec$', summary).group(1))) 

    avg_bw = sum(summed_bandwidth_values) / len(summed_bandwidth_values) 
    return (avg_bw / HOST_LINK_BW) * 100


if __name__ == "__main__":

    cwd = os.path.dirname(os.path.realpath(sys.argv[0]))

    parser = argparse.ArgumentParser(description="Generate Jellyfish Figure 9.")
    parser.add_argument('--debug', help='pins RNG and allows debug output', action='store_true')
    parser.add_argument('--servers', help='Number of servers', default=20, type=int)
    parser.add_argument('--switches', help='Number of switches', default=32, type=int)
    parser.add_argument('--ports', help='Number of ports per switch', default=6, type=int)
    parser.add_argument('--pickle', help='Topology pickle output path (should be relative to top-level repo dir)', default='pox/pox/ext/test_topo.pickle')
    parser.add_argument('--figure9', help='Output path for Figure 9 (.eps file), defaults to `figure9.eps`', default='figure9.eps')
    args = parser.parse_args()

    cleanmn()

    ##### FIGURE 9 #####

    # Generate full graph of randomly connected switches
    print "\nGenerating Figure 9\n===================\n"
    full_topo = generate_topology(n_servers=686, n_switches=245, n_ports=14, debug=args.debug)

    # Calculate the random permutation traffic paths across the graph
    link_paths = []
    link_paths.append(generate_path_counts(full_topo, 'k-shortest', 8, 18))
    link_paths.append(generate_path_counts(full_topo, 'ecmp', 64, 13))
    link_paths.append(generate_path_counts(full_topo, 'ecmp', 8, 10))

    # Summarize measurements and define display options
    cumulative_count_list = [summarize(lps) for lps in link_paths]
    format_options = [
        {
            'label': '8 Shortest Paths',
            'color': (0.204, 0.216, 0.592),
            'linewidth': 4,
            'solid_capstyle': 'round',
            'solid_joinstyle': 'round',
        },
        {
            'label': '64-way ECMP',
            'color': (0.792, 0.208, 0.220),
            'linewidth': 2,
            'markersize': 3,
            'dash_capstyle': 'round',
            'dash_joinstyle': 'round',
            'linestyle': ':',
        },
        {
            'label': '8-way ECMP',
            'color': (0.086, 0.620, 0.098),
            'linewidth': 2,
            'solid_capstyle': 'round',
            'solid_joinstyle': 'round',
        }
    ]
    generate_figure(cumulative_count_list, format_options, args.figure9)

    ##### TABLE 1 #####

    print "\nGenerating Table 1\n=================="
    print "will take quite a while; using %d Mb links\n" % (HOST_LINK_BW)
    test_topo = generate_topology(n_servers=args.servers, n_switches=args.switches, n_ports=args.ports, debug=args.debug)
    topo_path = os.path.join(cwd, args.pickle)
    if args.pickle:
        with open(topo_path, 'wb') as f:
            pickle.dump(test_topo, f)

    values = {
        ("ecmp", 1): parse_one_flow_output(run_table_test(cwd, topo_path, "ecmp", 1)),
        ("ecmp", 8): parse_multi_flow_output(run_table_test(cwd, topo_path, "ecmp", 8)),
        ("kshort", 1): parse_one_flow_output(run_table_test(cwd, topo_path, "kshort", 1)),
        ("kshort", 8): parse_multi_flow_output(run_table_test(cwd, topo_path, "kshort", 8)),
    }

    # Print table
    print
    print "            Jellyfish (%d svrs)" % (args.servers)       
    print "            ECMP \t 8-shortest paths"
    print "           --------------------------"
    print "TCP 1 Flow | " + str(values[("ecmp", 1)])[:4] + "% \t " + str(values[("kshort", 1)])[:4] + "%"
    print "TCP 8 Flow | " + str(values[("ecmp", 8)])[:4] + "% \t " + str(values[("kshort", 8)])[:4] + "%"

    print
    print "Reproduction script completed successfully"

