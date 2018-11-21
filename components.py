from events import *
from collections import deque
from queue import PriorityQueue

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

    def update_table(self, network):
        """
        Actual link state not implemented yet
        network defined as dict (key, value) = (router, [(router, cost)])
        referenced by id

        updates routing table
        """
        N = len(network)
        dist = {self.i: 0} #not in dist = inf
        child = {self.i: []} #store self as -1 for termination
        vis = set([self.i])
        pq = PriorityQueue() #holds (dist, (start, end))
        assert(pq.empty())

        for router in network[self.i]:
            pq.put((router[1], (self.i, router[0])))

        while not pq.empty():
            top = pq.get()
            dist[top[1][1]] = top[0]
            if(top[1][0] in child):
                child[top[1][0]].append(top[1][1])
            else:
                child[top[1][0]] = [top[1][1]]
            for router in network[top[1][1]]:
                if(router[0] not in vis):
                    pq.put((top[0] + router[1],
                            (top[1][1], router[0])))
                    vis.add(router[0])
            
        #shortest distance information acquired

        def dfsUpdate(n, base):
            if(n not in child):
                return
            for i in child[n]:
                table[i] = base
                dfsUpdate(i)
        
        for nxtRt in child[self.i]:
            dfsUpdate(nxtRt, nxtRt)

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

        self.usable = True  # is this link physiclaly usable? could be disabled
        self.buffer = deque()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

    def set_usable(self, usable_status):
        #  can simulate a physical link cut
        self.usable = usable_status

    def on_packet_entry(self, t, entry_component, p):
        if self.debug:
            print("t={}: {}: packet entered from {}, packet details: {}".
                  format(round(t, 6), self.i, entry_component.i, p))
        if not self.usable:
            return  # i mean yes.

        if self.buffer_usage + p.size > self.buffer_capacity:
            return  # nice packet loss

        exit_end = 1 if entry_component == self.ends[0] else 0
        self.buffer.append((p, exit_end))
        if self.debug:
            print('{} enqueueing packet into buffer: ({}, end={})'.
                    format(self.i, p.i, exit_end))
        self.buffer_usage += p.size
        if len(self.buffer) == 1: # First packet
            self.transmit_next_packet(t)

    def transmit_next_packet(self, t):
        p, _ = self.buffer[0]
        self.em.enqueue(LinkBufferRelease(t + self.rate * p.size, self))

    def on_buffer_release(self, t):
        if not self.usable:
            return  # nothing can occur
        p, exit_end = self.buffer.popleft()
        self.em.enqueue(LinkExit(t + self.delay, self, exit_end, p))
        if self.buffer:
            self.transmit_next_packet(t)

    def on_packet_exit(self, t, exit_end, exiting_packet):
        if not self.usable:
            return  # nothing can occur

        if self.debug:
            print("t={}: {}: packet exited from end {}, packet details: {}".
                  format(round(t, 6), self.i, exit_end, exiting_packet))

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

        # 0: Nothing done
        # 1: h1 (Syn) sent by SRC
        # 2: h1 received by DST and h2 (SynAck) sent by DST
        # 3: h2 received by SRC and h3 (Ack) sent by SRC
        # 4: h3 received by DST
        self.handshake_status = 0

    def make_packet(self, packet_type):
        size = 8192 if packet_type == 'data' else 512
        p = Packet(i=self.i + 'P' + str(self.packet_counter),
                   source=self.source,
                   destination=self.destination,
                   flow=self,
                   packet_type=packet_type,
                   size=size)
        self.packet_counter += 1
        return p

    def consider_send(self, t):
        if self.amount_left > 0 and \
                        len(self.outstanding_packets) < self.window_size:

            if self.handshake_status == 0:
                p = self.make_packet(packet_type='h1')
                # TODO: Finish
                pass
            elif self.handshake_status == 1:
                # Wait for SRC to timeout on h1 or receive h2
                pass
            elif self.handshake_status == 2:
                # Wait for SRC to timeout on h2 or receive h3
                pass
            else:
                # SRC can send freely now

                p = self.make_packet(packet_type='data')

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
    # 'h1' - handshake 1, or Syn sent by SRC
    # 'h2' - handshake 2, or SynAck sent by DST after receiving h1 from SRC
    # 'h3' - handshake 3, or Ack sent by SRC after receiving h2 from SRC

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

