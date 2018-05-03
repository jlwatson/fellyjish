import argparse
import pickle
import pprint
import random
import sys
from time import sleep, time

from topology import generate_topology
from kshortest import k_shortest_paths


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate Jellyfish Figure 9.")
    parser.add_argument('--debug', help='static random seed', action='store_true')
    parser.add_argument('--pickle', help='Topology pickle output path', default=None)
    args = parser.parse_args()

    topo_map = generate_topology(n_servers=3, n_switches=6, n_ports=3, debug=args.debug)
    if args.pickle:
        with open(args.pickle, 'wb') as f:
            pickle.dump(topo_map, f)

    print
    print "Topology:"
    pprint.pprint(topo_map)
    print

    k_shortest = k_shortest_paths(topo_map, 3)
    print "k-Shortest Paths (k=3):"
    pprint.pprint(k_shortest)
    print


