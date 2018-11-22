from components import Link, Packet, Flow
from events import EventManager

class MockHost:
    def __init__(self, i):
        self.i = i
        self.times = []
        self.packets = []

    def on_packet_reception(self, t, p):
        self.times.append(t)
        self.packets.append(p)

em = EventManager()
h1 = MockHost('H1')
h2 = MockHost('H2')
f = Flow(em, 'F', h1, h2, 100)
l = Link(em, 'L', h1, h2, 1, 10, 100)  # rate 1, delay 10
l.on_packet_entry(0, Packet('P1', h1, h2, f, 0, 1))
l.on_packet_entry(0, Packet('P2', h1, h2, f, 0, 1))
l.on_packet_entry(0, Packet('P3', h1, h2, f, 0, 1))
l.on_packet_entry(0, Packet('P4', h1, h2, f, 0, 1))
l.on_packet_entry(0, Packet('P5', h1, h2, f, 0, 1))
em.run()
assert h2.times == [11, 12, 13, 14, 15]
