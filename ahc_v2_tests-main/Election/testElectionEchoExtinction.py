import time
from graph import *
import numpy as np
import matplotlib.pyplot as plt


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.NetworkLayer.GenericNetworkLayer import GenericNetworkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.Election.EchoExtinction import ElectionEchoExtinctionComponent

topo = Topology()

message_count = 0


class AdHocNode(GenericModel):

  def on_init(self, eventobj: Event):
    print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

  def on_message_from_top(self, eventobj: Event):
    self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

  def on_message_from_bottom(self, eventobj: Event):
    self.send_up(Event(self, EventTypes.MFRB, eventobj.eventcontent))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    # SUBCOMPONENTS
    self.appllayer = ElectionEchoExtinctionComponent("ElectionEchoExtinctionComponent", componentinstancenumber, topology=topology)
    self.netlayer = GenericNetworkLayer("NetworkLayer", componentinstancenumber, topology=topology)
    self.linklayer = GenericLinkLayer("LinkLayer", componentinstancenumber, topology=topology)
    # self.failuredetect = GenericFailureDetector("FailureDetector", componentid)

    self.components.append(self.appllayer)
    self.components.append(self.netlayer)
    self.components.append(self.linklayer)

    # CONNECTIONS AMONG SUBCOMPONENTS
    self.appllayer.connect_me_to_component(ConnectorTypes.DOWN, self.netlayer)
    # self.failuredetect.connectMeToComponent(PortNames.DOWN, self.netlayer)
    self.netlayer.connect_me_to_component(ConnectorTypes.UP, self.appllayer)
    # self.netlayer.connectMeToComponent(PortNames.UP, self.failuredetect)
    self.netlayer.connect_me_to_component(ConnectorTypes.DOWN, self.linklayer)
    self.linklayer.connect_me_to_component(ConnectorTypes.UP, self.netlayer)

    # Connect the bottom component to the composite component....
    self.linklayer.connect_me_to_component(ConnectorTypes.DOWN, self)
    self.connect_me_to_component(ConnectorTypes.UP, self.linklayer)

  def initiate_process(self):
    self.appllayer.initiate_process()


def main():
  # G = nx.Graph()
  # G.add_nodes_from([1, 2])
  # G.add_edges_from([(1, 2)])
  # nx.draw(G, with_labels=True, font_weight='bold')
  # plt.draw()
  global message_count
  fig, axes = plt.subplots(1, 7)
  fig.set_figheight(5)
  fig.set_figwidth(10)
  fig.tight_layout()
  time_arr = []
  message_count_arr = []

  for i in range(4, 9):

    start_time = time.time()

    g = Grid(i, ax= axes[i-4])
    topo.construct_from_graph(g.G, AdHocNode, GenericChannel)
    topo.start()

    for i in range(0,10):
      topo.nodes[i].initiate_process()

    end_time = time.time()
    time_arr.append(end_time-start_time)

    message_count_arr.append(message_count)
    message_count = 0

    g.plot()


  axes[5].plot(np.array([n**2 for n in range(4,9)]), np.array(message_count_arr))
  axes[6].plot(np.array([n**2 for n in range(4,9)]), np.array(time_arr))
  axes[5].set_ylabel('Messeage Count')
  axes[5].set_xlabel('Node Count')
  axes[6].set_ylabel('Time Passes in Seconds')
  axes[6].set_xlabel('Node Count')
  axes[5].set_title("Message Count by Node Count")
  axes[5].set_title("Time")
  #plt.show()
  # plt.show()  # while (True): pass
  cnt = 1
  while True:
    cnt = cnt +1 
    time.sleep(1)
    if cnt > 10:
      break

if __name__ == "__main__":
  main()