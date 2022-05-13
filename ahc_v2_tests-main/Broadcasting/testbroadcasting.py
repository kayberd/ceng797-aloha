import networkx as nx
import time

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.Broadcasting.Broadcasting import ControlledFlooding

class AdHocNode(GenericModel):
  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    # SUBCOMPONENTS
    self.broadcastservice = ControlledFlooding("SimpleFlooding", componentinstancenumber, topology=topology)
    self.linklayer = GenericLinkLayer("LinkLayer", componentinstancenumber, topology=topology)

    self.components.append(self.broadcastservice)
    self.components.append(self.linklayer)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.broadcastservice.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.broadcastservice)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)


def main():
  G = nx.random_geometric_graph(19, 0.5)
  topo = Topology()
  topo.construct_from_graph(G, AdHocNode, GenericChannel)
  topo.start()
  cnt = 1
  while True:
    cnt = cnt +1 
    time.sleep(1)
    if cnt > 5:
      break


if __name__ == "__main__":
  main()
