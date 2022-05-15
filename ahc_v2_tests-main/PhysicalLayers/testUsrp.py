import os
import sys
import time, random, math
from enum import Enum
from pickle import FALSE

from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessage
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.MacProtocol.CSMA import MacCsmaPPersistentConfigurationParameters, MacCsmaPPersistent
from adhoccomputing.Networking.PhysicalLayer.UsrpB210OfdmFlexFramePhy import UsrpB210OfdmFlexFramePhy
from adhoccomputing.Networking.MacProtocol.GenericMAC import GenericMac


# registry = ComponentRegistry()
# from ahc.Channels.Channels import FIFOBroadcastPerfectChannel
# from ahc.EttusUsrp.UhdUtils import AhcUhdUtils

# framers = FramerObjects()


# define your own message types
class AlohaNodeMessageTypes(Enum):
    ACK = "ACK"
    DATA = "DATA"


class AlohaNodeEventTypes(Enum):
    STARTBROADCAST = "startbroadcast"


def wait_randomly():
    wait_amount = math.ceil(random.random() * 10)
    time.sleep(wait_amount)
    print(f"Waited for {wait_amount} seconds!!! ")


class AlohaNode(GenericModel):
    _node_count = 4


    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None,
                 num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads,
                         topology)
        self.eventhandlers[AlohaNodeEventTypes.STARTBROADCAST] = self.on_startbroadcast
        # Configure the p-persisten MAC
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5)

        #self.appl = UsrpApplicationLayer("UsrpApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, topology=topology)
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber, configurationparameters=macconfig,
                                      uhd=self.phy.ahcuhd, topology=topology)

        #self.components.append(self.appl)
        self.components.append(self.phy)
        self.components.append(self.mac)

        # CONNECTIONS AMONG SUBCOMPONENTS
        # Connections are simple. From top to bottom NODE-> APP -> MAC -> Phy -> NODE
        # self.appl.connect_me_to_component(ConnectorTypes.UP, self)  # Not required if nodemodel will do nothing
        # self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.mac)

        self.connect_me_to_component(ConnectorTypes.DOWN, self.mac)
        self.mac.connect_me_to_component(ConnectorTypes.UP, self)
        self.mac.connect_me_to_component(ConnectorTypes.DOWN, self.phy)

        self.phy.connect_me_to_component(ConnectorTypes.UP, self.mac)
        #self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        self.sent_frame = 0
        self.succ_sent_frame = 0

    def create_ack(self, eventobj: Event) -> Event:
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        evt.eventcontent.header.messagetype = AlohaNodeMessageTypes.ACK
        evt.eventcontent.header.messageto = eventobj.eventcontent.header.messagefrom
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventcontent.payload
        return evt

    def create_frame(self, destination_node, eventobj: Event) -> Event:
        hdr = GenericMessageHeader(AlohaNodeMessageTypes.DATA, self.componentinstancenumber, destination_node)
        self.sent_frame += 1
        payload = ""
        broadcastmessage = GenericMessage(hdr, payload)
        evt = Event(self, EventTypes.MFRT, broadcastmessage)
        return evt

    def on_message_from_bottom(self, eventobj: Event):

        if self.componentinstancenumber == eventobj.eventcontent.header.messageto:
            if eventobj.eventcontent.header.messagetype == AlohaNodeMessageTypes.DATA:
                #print(f"I am Node.{self.componentinstancenumber}, received Frame from Node {eventobj.eventcontent.header.messagefrom}")
                evt = self.create_ack(eventobj)
                self.send_down(evt)

            elif eventobj.eventcontent.header.messagetype == AlohaNodeMessageTypes.ACK:
                self.succ_sent_frame += 1
                #print(f"Node.{self.componentinstancenumber}, received ACK from Node.{eventobj.eventcontent.header.messagefrom} For: {eventobj.eventcontent.payload}")

    def on_startbroadcast(self, eventobj: Event):
        destination_node = random.randint(0, 3)
        while destination_node == self.componentinstancenumber:
            destination_node = random.randint(0, 3)

        # print(f"I am Node.{self.componentinstancenumber}, sending a message to Node.{hdr.messageto}")
        evt = self.create_frame(destination_node, eventobj)
        self.send_down(evt)


class UsrpNode(GenericModel):
    def on_init(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None,
                 num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads,
                         topology)
        # SUBCOMPONENTS

        # Configure the p-persisten MAC
        macconfig = MacCsmaPPersistentConfigurationParameters(0.5)

        self.appl = AlohaNode("UsrpApplicationLayer", componentinstancenumber, topology=topology)
        self.phy = UsrpB210OfdmFlexFramePhy("UsrpB210OfdmFlexFramePhy", componentinstancenumber, topology=topology)
        self.mac = MacCsmaPPersistent("MacCsmaPPersistent", componentinstancenumber, configurationparameters=macconfig,
                                      uhd=self.phy.ahcuhd, topology=topology)

        self.components.append(self.appl)
        self.components.append(self.phy)
        self.components.append(self.mac)

        # CONNECTIONS AMONG SUBCOMPONENTS
        # Connections are simple. From top to bottom NODE-> APP -> MAC -> Phy -> NODE
        self.appl.connect_me_to_component(ConnectorTypes.UP, self)  # Not required if nodemodel will do nothing
        self.appl.connect_me_to_component(ConnectorTypes.DOWN, self.mac)

        self.mac.connect_me_to_component(ConnectorTypes.UP, self.appl)
        self.mac.connect_me_to_component(ConnectorTypes.DOWN, self.phy)

        # Connect the bottom component to the composite component....
        self.phy.connect_me_to_component(ConnectorTypes.UP, self.mac)
        self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)

        # self.phy.connect_me_to_component(ConnectorTypes.DOWN, self)
        # self.connect_me_to_component(ConnectorTypes.DOWN, self.appl)


def run_test(my_topology, wait_time, number_of_nodes, number_of_messages, finish_wait_time):

    i = 0
    # test for only 1 random node sending a message to another random node with waiting between messages, this basically tests failure rate
    print("Reporting the overall statistics")
    while i < number_of_messages:
        random_node = random.randint(0, number_of_nodes - 1)
        my_topology.nodes[random_node].appl.send_self(
            Event(my_topology.nodes[random_node], AlohaNodeEventTypes.STARTBROADCAST, None))
        time.sleep(wait_time)
        i = i + 1
    time.sleep(finish_wait_time)
    total_data_sent = 0
    total_ack_sent = 0
    total_data_received = 0
    total_ack_received = 0
    for node in range(number_of_nodes):
        node = my_topology.nodes[node]
        total_data_sent += node.sent_data_counter
        total_ack_sent += node.sent_ack_counter
        total_data_received += node.received_data_counter
        total_ack_received += node.received_ack_counter
        print(
            f"Node.{node.componentinstancenumber}, sent.{node.sent_data_counter} Data, received.{node.received_data_counter} Data, ACKed.{node.sent_ack_counter}, received.{node.received_ack_counter} ACKs")

    data_fail_rate = 1 - (total_data_received / total_data_sent)
    ack_fail_rate = 1 - (total_ack_received / total_ack_sent)
    total_fail_rate = 1 - ((total_data_received + total_ack_received) / (total_data_sent + total_ack_sent))
    example_payload = "Message10 from NODE-1"
    payload_size = sys.getsizeof(example_payload)
    print("Data message failure rate is:", data_fail_rate, " ACK message failure rate is:", ack_fail_rate,
          " Total failure rate is:", total_fail_rate)
    print("Average Throughput is: ", ((1 - total_fail_rate) * payload_size / wait_time), " bytes/sec")


def main():
    topo = Topology()
    number_of_nodes = 4
    # Note that the topology has to specific: usrp winslab_b210_0 is run by instance 0 of the component
    # Therefore, the usrps have to have names winslab_b210_x where x in (0 to nodecount-1)
    topo.construct_winslab_topology_without_channels(number_of_nodes, UsrpNode)
    # topo.construct_winslab_topology_with_channels(2, UsrpNode, FIFOBroadcastPerfectChannel)
    topo.start()

    run_test(topo, 0.1, number_of_nodes, 100, 5)


if __name__ == "__main__":
    main()
