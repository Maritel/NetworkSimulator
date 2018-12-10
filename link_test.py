from events import EventManager
from host import Host
from link import Link
from flow import Flow
from packet import Packet, DATA_PACKET_SIZE, CONTROL_PACKET_SIZE

class MockHost:
    def __init__(self, i):
        self.i = i
        self.times = []
        self.packets = []

    def on_reception(self, t, p):
        self.times.append(t)
        self.packets.append(p)

class MockFlow:
    def __init__(self, i):
        self.i = i

em = EventManager(logging=False)
h1 = MockHost('H1')
h2 = MockHost('H2')
f = MockFlow('F')
# rate 1 pkt/sec, delay 10s
l = Link(em, 'L', h1, h2, DATA_PACKET_SIZE, 10, DATA_PACKET_SIZE * 10, debug=False)
l.on_packet_entry(0, Packet('P1', f, h1, h2, False, False, False, 1, 0, DATA_PACKET_SIZE))
l.on_packet_entry(0, Packet('P2', f, h1, h2, False, False, False, 2, 0, DATA_PACKET_SIZE))
l.on_packet_entry(0, Packet('P3', f, h1, h2, False, False, False, 3, 0, DATA_PACKET_SIZE))
l.on_packet_entry(0, Packet('P4', f, h1, h2, False, False, False, 4, 0, DATA_PACKET_SIZE))
l.on_packet_entry(0, Packet('P5', f, h1, h2, False, False, False, 5, 0, DATA_PACKET_SIZE))
# print(l.buffer)
# print(h2.packets, h2.times)
em.run(stop_when_flows_done=False)
assert h2.times == [11, 12, 13, 14, 15]
