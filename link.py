from events import LinkBufferRelease, LinkExit
from collections import deque

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

        self.usable = True  # is this link physically usable? could be disabled
        self.buffer = deque()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

    def set_usable(self, usable_status):
        #  can simulate a physical link cut
        self.usable = usable_status

    def on_packet_entry(self, t, p):

        if self.debug:
            print("t={}: Link {} packet entry, details: {}".
                  format(round(t, 6), self, p))
        if not self.usable:
            if self.debug:
                print("t={}: Link {} disabled.".format(round(t, 6), self))
            return  # Packet loss.

        if self.buffer_usage + p.size > self.buffer_capacity:
            if self.debug:
                print("t={}: Link {} lost a packet.".format(round(t, 6), self))
            return  # Packet loss.

        self.buffer.append(p)

        if self.debug:
            print('t={}, Link {} enqueueing packet into buffer: {}'.
                  format(round(t, 6), self, p.i))

        self.buffer_usage += p.size
        if len(self.buffer) == 1: # First packet
            self.transmit_next_packet(t)

    def transmit_next_packet(self, t):
        if self.usable:
            # Only pay the transmission delay here.
            p = self.buffer[0]
            self.em.enqueue(LinkBufferRelease(t + p.size / self.rate, self))

    def on_buffer_release(self, t):
        if self.usable:
            p = self.buffer.popleft()
            self.em.enqueue(LinkExit(t + self.delay, self, p))
            if len(self.buffer) > 0:
                self.transmit_next_packet(t)

    def on_packet_exit(self, t, exiting_packet):
        if self.usable:
            if self.debug:
                print("t={}: Link {} packet exit, details: {}".
                      format(round(t, 6), self, exiting_packet))

            self.dest.on_reception(t, exiting_packet)

    def __str__(self):
        return "{} ({} -> {})".format(self.i, self.source.i, self.dest.i)