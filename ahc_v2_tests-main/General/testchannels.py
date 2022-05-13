import os
import sys
import time
import pdb, traceback, sys


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, GenericMessageHeader, GenericMessage
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel


import networkx as nx
import matplotlib.pyplot as plt


class SenderReceiver(GenericModel):
  def on_init(self, eventobj: Event):
    print("Initialized ", self.componentname, self.componentinstancenumber)
    self.sendcnt = 1
    self.recvcnt = 0
    if self.componentinstancenumber == 0:
      self.send_self(Event(self, "generatemessage", "..."))

  def on_generate_message(self, eventobj: Event):
    self.sendcnt = self.sendcnt + 1
    msg = GenericMessage(GenericMessageHeader("AL", 0, 1), str(self.sendcnt))
    self.send_down(Event(self, EventTypes.MFRT, msg))
    time.sleep(0.1)
    self.send_self(Event(self, "generatemessage", "..."))

  def on_message_from_bottom(self, eventobj: Event):
    self.recvcnt = self.recvcnt + 1
    self.sentcnt = int(eventobj.eventcontent.payload)
    print(f"{self.recvcnt / self.sentcnt}")
    msg = GenericMessage(GenericMessageHeader("AL", 0, 1), str(self.sendcnt))
    self.send_down(Event(self, EventTypes.MFRT, msg))

  def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
    super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
    self.eventhandlers["generatemessage"] = self.on_generate_message



def main():
  topo = Topology()
  topo.construct_sender_receiver(SenderReceiver, SenderReceiver, GenericChannel)
  nx.draw(topo.G, with_labels=True, font_weight='bold')
  plt.draw()

  # topo.computeForwardingTable()

  topo.start()
  plt.show()
  # while (True): pass   #plt.show() handles this

if __name__ == "__main__":
  try:
    main()
  except:
    extype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
