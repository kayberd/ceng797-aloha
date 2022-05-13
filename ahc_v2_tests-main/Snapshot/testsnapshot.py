#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.getcwd())

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.Snapshot.Snapshot import ChandyLamportComponentModel, LaiYangComponentModel, SnapshotEventTypes
import matplotlib.pyplot as plt
import networkx as nx


def main():
    topo = Topology()
    topo.construct_sender_receiver(ChandyLamportComponentModel,
                                   ChandyLamportComponentModel, GenericChannel)
    nx.draw(topo.G, with_labels=True, font_weight='bold')
    plt.draw()
    topo.start()
    topo.sender.send_self(Event(topo.sender, SnapshotEventTypes.TS, None))
    plt.show()

    topo.construct_sender_receiver(LaiYangComponentModel,
                                   LaiYangComponentModel, GenericChannel)
    nx.draw(topo.G, with_labels=True, font_weight='bold')
    plt.draw()
    topo.start()
    topo.sender.send_self(Event(topo.sender, SnapshotEventTypes.TS, None))
    plt.show()


if __name__ == "__main__":
    exit(main())
