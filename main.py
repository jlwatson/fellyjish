import argparse
import pickle
import pprint
import random
import sys
from time import sleep, time

from topology import generate_topology


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate Jellyfish Figure 9.")
    parser.add_argument('--debug', help='static random seed', action='store_true')
    parser.add_argument('--pickle', help='Topology pickle output path', default='topo.pickle')
    args = parser.parse_args()

    topo_map = generate_topology(n_servers=3, n_switches=6, n_ports=3, debug=args.debug)
    pprint.pprint(topo_map)

    with open(args.pickle, 'wb') as f:
        pickle.dump(topo_map, f)

