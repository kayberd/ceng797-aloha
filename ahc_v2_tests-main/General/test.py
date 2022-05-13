import os
import sys
import time
import random
from enum import Enum

sys.path.insert(0, os.getcwd())

import networkx as nx
import matplotlib.pyplot as plt


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes, GenericMessageHeader, GenericMessagePayload, GenericMessage
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.NetworkLayer.GenericNetworkLayer import GenericNetworkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel


# define your own message types
class ApplicationLayerMessageTypes(Enum):
    PROPOSE = "PROPOSE"
    ACCEPT = "ACCEPT"


# define your own message header structure
class ApplicationLayerMessageHeader(GenericMessageHeader):
    pass


# define your own message payload structure
class ApplicationLayerMessagePayload(GenericMessagePayload):
    pass


class ApplicationLayerComponent(GenericModel):
    def on_init(self, eventobj: Event):
        print(f"Initializing {self.componentname}.{self.componentinstancenumber}")

        if self.componentinstancenumber == 0:
            # destination = random.randint(len(Topology.G.nodes))
            destination = 1
            hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.PROPOSE, self.componentinstancenumber,
                                                destination)
            payload = ApplicationLayerMessagePayload("23")
            proposalmessage = GenericMessage(hdr, payload)
            randdelay = random.randint(0, 5)
            time.sleep(randdelay)
            self.send_self(Event(self, "propose", proposalmessage))
        else:
            pass

    def on_message_from_bottom(self, eventobj: Event):
        try:
            applmessage = eventobj.eventcontent
            hdr = applmessage.header
            if hdr.messagetype == ApplicationLayerMessageTypes.ACCEPT:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
            elif hdr.messagetype == ApplicationLayerMessageTypes.PROPOSE:
                print(
                    f"Node-{self.componentinstancenumber} says Node-{hdr.messagefrom} has sent {hdr.messagetype} message")
        except AttributeError:
            print("Attribute Error")

    # print(f"{self.componentname}.{self.componentinstancenumber}: Gotton message {eventobj.content} ")
    # value = eventobj.content.value
    # value += 1
    # newmsg = MessageContent( value )
    # myevent = Event( self, "agree", newmsg )
    # self.trigger_event(myevent)

    def on_propose(self, eventobj: Event):
        destination = 1
        hdr = ApplicationLayerMessageHeader(ApplicationLayerMessageTypes.ACCEPT, self.componentinstancenumber,
                                            destination)
        payload = ApplicationLayerMessagePayload("23")
        proposalmessage = GenericMessage(hdr, payload)
        self.send_down(Event(self, EventTypes.MFRT, proposalmessage))

    def on_agree(self, eventobj: Event):
        print(f"Agreed on {eventobj.eventcontent}")

    def on_timer_expired(self, eventobj: Event):
        pass

    def __init__(self, componentname, componentinstancenumber, context=None, configurationparameters=None, num_worker_threads=1, topology=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads, topology)
        self.eventhandlers["propose"] = self.on_propose
        self.eventhandlers["agree"] = self.on_agree
        self.eventhandlers["timerexpired"] = self.on_timer_expired


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
        self.appllayer = ApplicationLayerComponent("ApplicationLayer", componentinstancenumber, topology=topology)
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


def main():
    # G = nx.Graph()
    # G.add_nodes_from([1, 2])
    # G.add_edges_from([(1, 2)])
    # nx.draw(G, with_labels=True, font_weight='bold')
    # plt.draw()
    G = nx.random_geometric_graph(19, 0.5)
    nx.draw(G, with_labels=True, font_weight='bold')
    plt.draw()

    topo = Topology()
    topo.construct_from_graph(G, AdHocNode, GenericChannel)
    topo.start()

    plt.show()  # while (True): pass


if __name__ == "__main__":
    main()
