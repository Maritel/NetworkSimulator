from events import *
import queue


class Host(object):
    def __init__(self, event_manager, i, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        self.link = None  # link that this host can access
        self.debug = debug
    
    def add_link(self, link):
        if self.link is not None:
            raise ValueError('Link already added')
        self.link = link

    def on_packet_reception(self, t, p):
        if self.debug:
            print("t={}: {}: packet received: {}".
                  format(round(t, 6), self.i, p))

        assert p.destination == self
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
            if self.debug:
                print("t={}: {}: creating ack packet: {}".
                      format(round(t, 6), self.i, ack_packet))
            self.link.on_packet_entry(t, self, ack_packet)


class Router(object):
    def __init__(self, event_manager, i, table=None, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        # Routing table for routers
        self.table = table  # dict(ID -> ID)
        self.links = []  # links that this router can access
        self.debug = debug

    def add_link(self, link):
        self.links.append(link)

    def on_packet_reception(self, t, p):
        if self.debug:
            print("t={}: {}: packet received: {}".
                  format(round(t, 6), self.i, p))
        #assume self.table is table[destID] = linkID
        #assume routing is instantaneous
        #silently fail
        nextLink = self.links[self.table[p.destination.id]]
        try:
            nextLink.on_packet_entry(t, self.i, p)
            return True
        except:
            return False


class Link(object):
    def __init__(self, event_manager, i, end_a, end_b, rate, delay,
                 buffer_capacity, debug=True):
        self.debug = debug

        self.em = event_manager
        self.i = i
        self.ends = (end_a, end_b)  # Each end is either a router or a host
        self.rate = rate  # bits per second
        self.delay = delay  # seconds

        self.queue_connected = True #queue connected to link?
        self.free = True  # currently unused? Buffer packets count as use.
        self.buffer = queue.Queue()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

    def disrupt(self, connect=False):
        #simulate a physical link cut
        self.queue_connected = connect
    
    def on_packet_entry(self, t, entry_component, p):
        if self.debug:
            print("t={}: {}: packet entered from {}, packet details: {}".
                  format(round(t, 6), self.i, entry_component.i, p))

        exit_end = 1 if entry_component == self.ends[0] else 0

        #make sure buffer is still attached to queue
        assert self.queue_connected
        
        if self.free:
            traversal_time = self.delay + p.size / self.rate
            self.free = False
            self.em.enqueue(LinkExit(t + traversal_time, self, exit_end, p))
        elif self.buffer_usage + p.size > self.buffer_capacity:
            return  # nice packet loss
        else:
            self.buffer.put((p, exit_end))
            if self.debug:
                print('{} enqueueing packet into buffer: ({}, end={})'.
                      format(self.i, p.i, exit_end))
            self.buffer_usage += p.size

            
    def on_packet_exit(self, t, exit_end, exiting_packet):
        if self.debug:
            print("t={}: {}: packet exited from end {}, packet details: {}".
                  format(round(t, 6), self.i, exit_end, exiting_packet))

        #make sure buffer is still attached to link
        assert self.queue_connected
        assert not self.free
        
        if self.buffer_usage == 0:
            self.free = True
        else:
            next_p, next_p_exit_end = self.buffer.get()
            if self.debug:
                print('{} dequeueing packet from buffer: ({}, end={})'.
                      format(self.i, next_p.i, exit_end))

            self.buffer_usage -= next_p.size
            traversal_time = self.delay + next_p.size / self.rate
            self.em.enqueue(LinkExit(t + traversal_time, self,
                                     next_p_exit_end, next_p))

        self.ends[exit_end].on_packet_reception(t, exiting_packet)


class Flow(object):
    def __init__(self, event_manager, i, source, destination, amount,
                 debug=True):
        self.debug = debug

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

            if self.debug:
                print("t={}, {} sends packet {}".
                      format(round(t, 6), self.i, p))

            self.em.enqueue(FlowAckTimeout(t + self.ack_wait_time, self, p))
            self.source.link.on_packet_entry(t, self.source, p)
            self.consider_send(t)  # Send as much as possible.
        else:
            # If there's outstanding packets, then either the timeout or the
            # reception of an Ack will trigger action.
            return None

    def on_ack_timeout(self, t, timed_out_packet):
        if timed_out_packet in self.outstanding_packets:
            self.outstanding_packets.remove(timed_out_packet)

            # TODO: modify parameters more intelligently
            self.ack_wait_time *= 2

            self.consider_send(t)

            if self.debug:
                print("t={}: {}: ack timeout for packet: {}".
                      format(round(t, 6), self.i, timed_out_packet))

        else:
            pass  # Was previously acknowledged successfully.

    def on_ack_reception(self, t, acked_packet):
        if acked_packet in self.outstanding_packets:
            self.outstanding_packets.remove(acked_packet)
            self.amount_left -= acked_packet.size
            self.consider_send(t)


class Packet(object):
    # TYPES OF PACKETS:
    # 'data'
    # 'ack'

    def __init__(self, i, source, destination, flow, packet_type, size,
                 info=None, debug=True):
        self.i = i
        self.source = source
        self.destination = destination
        self.flow = flow
        self.packet_type = packet_type
        self.size = size  # bits
        self.info = info
        self.debug = debug

    def __str__(self):
        return "(id: {}, src: {}, dst: {}, " \
               "flow: {}, type: {}, " \
               "size: {})".format(self.i, self.source.i, self.destination.i,
                                 self.flow.i, self.packet_type, self.size)

