import os
import sys
import time, random, math
from enum import Enum
from pickle import FALSE

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessage
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistent, MacCsmaPPersistentConfigurationParameters


# registry = ComponentRegistry()
# from ahc.Channels.Channels import FIFOBroadcastPerfectChannel
# from ahc.EttusUsrp.UhdUtils import AhcUhdUtils

# framers = FramerObjects()


# define your own message types
class ApplicationLayerMessageTypes(Enum):
    BROADCAST = "BROADCAST"
    SYN = "SYN"
    ACK = "ACK"
    DATA = "DATA"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


class UsrpApplicationLayerEventTypes(Enum):
    STARTBROADCAST = "startbroadcast"


class UsrpApplicationLayer(GenericModel):
    node_count = 4

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None,
                 num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads,
                         topology)
        self.eventhandlers[UsrpApplicationLayerEventTypes.STARTBROADCAST] = self.on_startbroadcast
        self.sent_message_counter = 0
        self.succ_sent_message_counter = 0

    def on_message_from_top(self, eventobj: Event):
        self.send_down(Event(self, EventTypes.MFRT, eventobj.eventcontent))

    def on_message_from_bottom(self, eventobj: Event):
        if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
            if eventobj.eventcontent.header.messagetype == ApplicationLayerMessageTypes.DATA:
                print(
                    f"I am Node-{self.componentinstancenumber}, received DATA from Node-{eventobj.eventcontent.header.messagefrom}")
                evt = self.create_ack(eventobj)
                self.send_down(evt)

            elif eventobj.eventcontent.header.messagetype == ApplicationLayerMessageTypes.ACK:
                self.succ_sent_message_counter += 1
                print(
                    f"Node.{self.componentinstancenumber}, received ACK from Node.{eventobj.eventcontent.header.messagefrom}")

    def on_startbroadcast(self, eventobj: Event):
        dest_node = random.randint(0, 3)
        while dest_node == self.componentinstancenumber:
            dest_node = random.randint(0, self.node_count - 1)

        evt = self.create_frame(dest_node, eventobj)
        print(f"I am Node-{self.componentinstancenumber}, sending DATA to Node-{dest_node}")
        self.send_down(evt)

    def create_ack(self, eventobj: Event) -> Event:
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        evt.eventcontent.header.messagetype = ApplicationLayerMessageTypes.ACK
        evt.eventcontent.header.messageto = eventobj.eventcontent.header.messagefrom
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload
        return evt

    def create_frame(self, destination_node, eventobj: Event) -> Event:
        header = GenericMessageHeader(ApplicationLayerMessageTypes.DATA, self.componentinstancenumber, destination_node)
        self.sent_message_counter += 1
        payload = ""
        broadcastmessage = GenericMessage(header, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        return evt


class UsrpNode(GenericModel):

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None,
                 num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads,
                         topology)
        # SUBCOMPONENTS

        macconfig = MacCsmaPPersistentConfigurationParameters(0.5)

        self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, topology=topology)
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber, configurationparameters=macconfig,
                                      uhd=self.phy.ahcuhd, topology=topology)

        self.components.append(self.appl)
        self.components.append(self.phy)
        self.components.append(self.mac)

        # CONNECTIONS AMONG SUBCOMPONENTS
        self.appl.connect_me_to_component(ConnectorTypes.UP, self)  # Not required if nodemodel will do nothing
        self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.mac)

        self.mac.connect_me_to_component(ConnectorTypes.UP, self.appl)
        self.mac.connect_me_to_component(ConnectorTypes.DOWN, self.phy)

        # Connect the bottom component to the composite component....
        self.phy.connect_me_to_component(ConnectorTypes.UP, self.mac)
        self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)

        # self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        # self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)


def run_test(topology:Topology,num_of_msg:int,):

    for msg_index in range(0,num_of_msg):
        rand_node: UsrpNode = topology.nodes[random.randint(0, len(topology.nodes)-1)]
        broadcast_event = Event(rand_node, UsrpApplicationLayerEventTypes.STARTBROADCAST, eventcontent=None)
        rand_node.appl.send_self(broadcast_event)


def main():

    topo = Topology()
    topo.construct_winslab_topology_without_channels(4, UsrpNode)
    topo.start()

    num_of_msg = 10
    run_test(topo, num_of_msg)


if __name__ == "__main__":
    main()
