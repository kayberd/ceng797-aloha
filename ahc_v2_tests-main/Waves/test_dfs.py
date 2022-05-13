import os
import sys
import random
import time

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.Waves.DepthFirstSearch import DfsTraverse

class MyTopo(Topology):
  def __init__(self, name=None) -> None:
      super().__init__(name)

  def construct_my_topology(self):
    pass

class AdHocNode(GenericModel):
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))
    print(self.componentname, "-", self.componentinstancenumber, " received a message from top")

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))
    print(self.componentname, "-", self.componentinstancenumber, " received a message from bottom")

  def on_init(self, eventobj:Event):
    #print("initialized", self.componentname)
    pass

  def __init__(self, componentname, componentid, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentid, context, configurationparameters, num_worker_threads, topology)
    # SUBCOMPONENTS
    #print("testdfs_topology", topology)
    self.traverse_service = DfsTraverse("DfsTraverse", componentid,topology = topology)
    self.link_layer = GenericLinkLayer("LinkLayer", componentid,topology = topology)
    
    self.components.append(self.traverse_service)
    self.components.append(self.link_layer)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.traverse_service.connect_me_to_component(ConnectorTypes.DOWN, self.link_layer)
    self.link_layer.connect_me_to_component(ConnectorTypes.UP, self.traverse_service)

    # Connect the bottom component to the composite component....
    self.link_layer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.link_layer)



def main():
  G = nx.random_geometric_graph(9, 0.8, seed=5)
  nx.draw(G, with_labels=True, font_weight='bold')
  plt.draw()

  topo = MyTopo("MyTopology")
  topo.construct_from_graph(G, AdHocNode, GenericChannel)

  topo.start()
  time.sleep(1)
  
  random.seed(10)
  random_node:AdHocNode = topo.get_random_node()
  random_node.traverse_service.start_traverse()
  plt.show()

if __name__ == "__main__":
  main()
