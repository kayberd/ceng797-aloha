import queue
from enum import Enum

from adhoccomputing.Generics import Event, EventTypes
from adhoccomputing.Networking.MacProtocol.GenericMAC import GenericMac
import time
from random import randint

T_P = 1000  # Max propagation time in ms.


class AlohaEventTypes(Enum):
    ACK = "ACK"
    DATA = "DATA"


class PacketUnit:
    K_MAX = 15

    def __init__(self, event: Event):
        self.event = event
        self.K = 0
        self.send_time = time.time() * 1000

    def get_back_off_time(self):
        R = randint(0, 2 ** self.K - 1)
        return T_P ** R

    def is_expired(self):
        return self.K > self.K_MAX

    def should_resend(self):
        return time.time() * 1000 - self.send_time > T_P


class AlohaNode(GenericMac):
    def __init__(self, componentname, componentinstancenumber, context=None,
                 configurationparameters=None,
                 num_worker_threads=1, topology=None, sdr=None):
        super().__init__(componentname, componentinstancenumber, context, configurationparameters, num_worker_threads,
                         topology, sdr)

        self.not_acked_packets: [PacketUnit] = []

    def update_not_acked_packets(self):
        for packet in self.not_acked_packets:
            if packet.should_resend:
                packet.K = packet.K + 1
                packet.send_time = time.time() * 1000

    def on_ack(self, ack: Event):
        filter(lambda packet: not (packet.event.eventid == ack.eventcontent.payload or packet.is_expired()),
               self.not_acked_packets)

    def on_init(self, eventobj: Event):
        super().on_init(eventobj)

    def on_message_from_bottom(self, eventobj: Event):
        """ Message from link physical layer message goes into inbox """
        if eventobj.eventcontent.header.messagetype == AlohaEventTypes.ACK:
            self.on_ack(ack=eventobj)
        else:
            if not self.not_acked_packets:
                self.send_ack(eventobj)
                self.send_up(eventobj)

    def send_ack(self, eventobj: Event):
        evt = Event(self, EventTypes.MFRT, eventobj.eventcontent)
        evt.eventcontent.header.messagetype = AlohaEventTypes.ACK
        evt.eventcontent.header.messageto = eventobj.eventcontent.header.messagefrom
        evt.eventcontent.header.messagefrom = self.componentinstancenumber
        evt.eventcontent.payload = eventobj.eventid
        self.send_down(evt)  # Send the ACK

    def on_message_from_top(self, eventobj: Event):
        """ Message from link link layer message goes into outer """
        packet = PacketUnit(event=eventobj)
        self.not_acked_packets.append(packet)
        self.update_not_acked_packets()
        head = self.not_acked_packets[0]
        self.send_down(head.event)

