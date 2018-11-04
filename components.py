from events import *
import queue


class Host(object):
    def __init__(self, event_manager, i):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        self.link = None  # link that this host can access

    def on_packet_reception(self, t, p):
        assert p.destination is self
        if p.packet_type == 'ack':
            acked_packet = p.info
            p.flow.on_ack_reception(t, acked_packet)
        elif p.packet_type == 'data':
            # Create acknowledgement packet and send it.
            ack_packet = Packet(i='A' + p.i,
                                source=self,
                                destination=p.source,
                                flow=p.flow,
                                packet_type='ack',
                                size=512,
                                info=p)
            self.link.on_packet_entry(t, self, ack_packet)

class Router(object):
    def __init__(self, event_manager, i, table=None):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        # Routing table for routers
        self.table = table  # dict(ID -> ID)
        self.links = []  # links that this router can access

    def on_packet_reception(self, t, p):
        pass


class Link(object):
    def __init__(self, event_manager, i, end_a, end_b, rate, delay,
                 buffer_capacity):
        self.em = event_manager
        self.i = i
        self.ends = (end_a, end_b)  # Each end is either a router or a host
        self.rate = rate  # bits per second
        self.delay = delay  # seconds

        self.free = True  # currently unused? Buffer packets count as use.
        self.buffer = queue.Queue()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

    def on_packet_entry(self, t, source, p):
        exit_end = 1 if source is self.ends[0] else 0
        if self.free:
            traversal_time = self.delay + p.size / self.rate
            self.free = False
            self.em.enqueue(LinkExit(t + traversal_time, self, exit_end, p))
        elif self.buffer_usage + p.size > self.buffer_capacity:
            return  # nice packet loss
        else:
            self.buffer.put((p, exit_end))
            self.buffer_usage += p.size

    def on_packet_exit(self, t, exit_end, exiting_packet):
        assert not self.free
        if self.buffer_usage == 0:
            self.free = True
        else:
            buffer_packet, exit_end = self.buffer.get()
            self.buffer_usage -= buffer_packet.size()
            traversal_time = self.delay + buffer_packet.size / self.rate
            self.em.enqueue(LinkExit(t + traversal_time, self, exit_end,
                                     buffer_packet))

        self.ends[exit_end].on_packet_reception(t, exiting_packet)


class Flow(object):
    def __init__(self, event_manager, i, source, destination, amount):
        self.em = event_manager
        self.i = i
        self.source = source # should be a host
        self.destination = destination
        self.amount_left = amount  # bits; amount of unack'ed data left to send

        self.outstanding_packets = set([])  # packets we don't know about
        self.window_size = 1  # max size of 'outstanding packets'
        self.packet_counter = 1
        self.ack_wait_time = 0.1  # in seconds

    def consider_send(self, t):
        if self.amount_left > 0 and \
                        len(self.outstanding_packets) < self.window_size:

            p = Packet(i=self.i + 'P' + str(self.packet_counter),
                       source=self.source,
                       destination=self.destination,
                       flow=self,
                       packet_type='data',
                       size=8192)
            self.packet_counter += 1
            self.outstanding_packets.add(p)

            self.em.enqueue(FlowAckTimeout(t + self.ack_wait_time, self, p))
            self.source.link.on_packet_entry(t, self.source, p)
            self.consider_send(t)  # Send as much as possible.
        else:
            # If there's outstanding packets, then either the timeout or the
            # reception of an Ack will trigger action.
            return None

    def on_ack_timeout(self, t, p):
        if p in self.outstanding_packets:
            self.outstanding_packets.remove(p)
            # TODO: modify parameters
            self.consider_send(t)
        else:
            pass # Was acknowledged successfully.

    def on_ack_reception(self, t, acked_packet):
        self.outstanding_packets.remove(acked_packet)
        self.amount_left -= acked_packet.size
        self.consider_send(t)


class Packet(object):
    # TYPES OF PACKETS:
    # 'data'
    # 'ack'

    def __init__(self, i, source, destination, flow, packet_type, size,
                 info=None):
        self.i = i
        self.source = source
        self.destination = destination
        self.flow = flow
        self.packet_type = packet_type
        self.size = size  # bits
        self.info = info

