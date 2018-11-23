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

        self.usable = True  # is this link physiclaly usable? could be disabled
        self.buffer = deque()
        self.buffer_usage = 0
        self.buffer_capacity = buffer_capacity  # bits

    def set_usable(self, usable_status):
        #  can simulate a physical link cut
        self.usable = usable_status

    def on_packet_entry(self, t, p):
        if self.debug:
            print("t={}: {} (from {} to {}) packet entry, details: {}".
                  format(round(t, 6), self.i, self.source.i, self.dest.i, p))
        if not self.usable:
            return  # i mean yes.

        if self.buffer_usage + p.size > self.buffer_capacity:
            return  # nice packet loss

        self.buffer.append(p)
        if self.debug:
            print('{} (from {} to {}) enqueueing packet into buffer: {}'.
                    format(self.i, self.source.i, self.dest.i, p.i))
        self.buffer_usage += p.size
        if len(self.buffer) == 1: # First packet
            self.transmit_next_packet(t)

    def transmit_next_packet(self, t):
        p = self.buffer[0]
        self.em.enqueue(LinkBufferRelease(t + self.rate * p.size, self))

    def on_buffer_release(self, t):
        if not self.usable:
            return  # nothing can occur
        p = self.buffer.popleft()
        self.em.enqueue(LinkExit(t + self.delay, self, p))
        if self.buffer:
            self.transmit_next_packet(t)

    def on_packet_exit(self, t, exiting_packet):
        if not self.usable:
            return  # nothing can occur

        if self.debug:
            print("t={}: {} (from {} to {}) packet exit, details: {}".
                  format(round(t, 6), self.i, self.source.i, self.dest.i, exiting_packet))

        self.dest.on_reception(t, exiting_packet)