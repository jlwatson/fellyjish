import argparse
import build_topology
import pickle
import random
import sys
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
from build_topology import JellyFishTop


def experiment(net):
    net.start()
    dumpNetConnections(net)
    sleep(3)
    net.ping(net.hosts[:2])
    net.stop()


def main(topo_pickle_path):

    with open(topo_pickle_path, 'rb') as f:
        topo = pickle.load(f)
        net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
        experiment(net)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run fellyjish experiment.")
    parser.add_argument('--pickle', help='Topo pickle file path', default='topo.pickle')
    args = parser.parse_args()

    main(args.pickle)

