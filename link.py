from events import Event
from collections import deque
from packet import LinkStatePacket

class Link(object):
    def __init__(self, event_manager, i, source, dest, rate, delay,
                 buffer_capacity, debug=True):
        self.debug = debug

        self.em = event_manager
        self.i = i
        self.source = source  # Each end is either a router or a host
        self.dest = dest
        self.rate = rate  # bits per second
        self.delay = delay  # seconds
        
        self.usable = True  # Whether the link accepts new packets
        self.buffer = deque()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

        self.interval_usage = 0 #total buffer usage since last linkstate req
        
    def set_usable(self, usable_status):
        #  can simulate a physical link cut
        self.usable = usable_status

    def on_packet_entry(self, t, p):
        if not self.usable:
            if self.debug:
                print("t={}: Link {} disabled.".format(round(t, 6), self))
            return  # Packet loss.
        if self.buffer_usage + p.size > self.buffer_capacity:
            if self.debug:
                print("t={}: Link {} lost a packet.".format(round(t, 6), self))
            ### Per-link packet loss ###
            self.em.log_it('LINK|{}'.format(self.i), 'T|{}|LOSS|1'.format(t))
            return  # Packet loss.

        self.buffer.append(p)
        self.update_buffer_usage(t, p.size)
        self.interval_usage += p.size
        
        if self.debug and type(p) is not LinkStatePacket:
            print('t={}, Link {} enqueueing packet into buffer: {}'.
                  format(round(t, 6), self, p.i))

        if len(self.buffer) == 1: # First packet
            self.transmit_next_packet(t)

    def transmit_next_packet(self, t):
        # Only pay the transmission delay here.
        p = self.buffer[0]
        self.em.enqueue(LinkBufferRelease(t + p.size / self.rate, self))

    def on_buffer_release(self, t):
        p = self.buffer.popleft()
        self.update_buffer_usage(t, -p.size)

        self.em.enqueue(LinkExit(t + self.delay, self, p))
        if len(self.buffer) > 0:
            self.transmit_next_packet(t)

    def update_buffer_usage(self, t, amount):
        self.buffer_usage += amount
        ### Per-link buffer occupancy ###
        self.em.log_it('LINK|{}'.format(self.i), 'T|{}|BUFF|{}'.format(t, amount))

    def on_packet_exit(self, t, exiting_packet):
        if self.debug and type(exiting_packet) is not LinkStatePacket:
            print("t={}: Link {} packet exit, details: {}".
                    format(round(t, 6), self, exiting_packet))

        self.dest.on_reception(t, exiting_packet)
        ### Per-link flow rate ###
        self.em.log_it('LINK|{}'.format(self.i), 'T|{}|FLOW|{}'.format(t, exiting_packet.size))

    def __str__(self):
        return "{} ({} -> {})".format(self.i, self.source.i, self.dest.i)

    def __eq__(self, other):
        return self.i == other.i if isinstance(other, Link) else False

    def __hash__(self):
        return hash(self.i)


class LinkBufferRelease(Event):
    # When a packet is released from the link's buffer.
    def __init__(self, t, link):
        super().__init__(t)
        self.link = link

    def run(self):
        self.link.on_buffer_release(self.t)


class LinkExit(Event):
    # When a packet reaches the end of a link.
    def __init__(self, t, link, packet):
        super().__init__(t)
        self.link = link
        self.packet = packet

    def run(self):
        self.link.on_packet_exit(self.t, self.packet)


class LinkSetUsable(Event):
    def __init__(self, t, link, usable):
        super().__init__(t)
        self.link = link
        self.usable = usable
    
    def run(self):
        self.link.set_usable(self.usable)
