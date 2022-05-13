import os
import sys
import networkx as nx
import matplotlib.pyplot as plt

sys.path.insert(0, os.getcwd())

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.Waves.TreeAlgorithm import TreeNode



def startTreeAlgorithm(treeTopology):
  for node in treeTopology.nodes.values():
    node.startTreeAlgorithm()

def main():

  G = nx.random_geometric_graph(190, 0.5)
  MST = nx.minimum_spanning_tree(G)

  nx.draw(MST, with_labels=True, font_weight='bold')
  plt.draw()

  topo = Topology()
  topo.construct_from_graph(MST, TreeNode, GenericChannel)
  topo.start()
  startTreeAlgorithm(topo)


  plt.show()  

if __name__ == "__main__":
  main()