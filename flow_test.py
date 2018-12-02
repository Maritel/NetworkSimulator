from congestion_control import StopAndWait
from events import EventManager
from host import Host
from link import Link
from flow import Flow
from packet import Packet, DATA_PACKET_SIZE, CONTROL_PACKET_SIZE

class PacketRecorder:
    def __init__(self, next_component):
        self.next_component = next_component
        self.packets = []

    def on_reception(self, t, p):
        self.packets.append(p)
        self.next_component.on_reception(t, p)

em = EventManager(logging=False)
host_1 = Host(em, 'H1', debug=True)
p1 = PacketRecorder(host_1)
host_2 = Host(em, 'H2', debug=True)
p2 = PacketRecorder(host_2)
l1_a = Link(em, 'L1_a', host_1, p2, 10485760, 0.01, 524288, debug=False)
l1_b = Link(em, 'L1_b', host_2, p1, 10485760, 0.01, 524288, debug=False)
host_1.link = l1_a
host_2.link = l1_b
flow = Flow(em, 'F1', host_1, host_2, DATA_PACKET_SIZE, 1, StopAndWait(), debug=True)
em.run()

# Packets sent by host 1
p2_expect = [
    # SYN
    Packet('F11', flow, host_1, host_2, syn_flag = True, ack_flag = False,
           fin_flag = False, seq_number = 0, ack_number = None, size = CONTROL_PACKET_SIZE),
    # ACK of SYN
    Packet('F13', flow, host_1, host_2, syn_flag = False, ack_flag = True,
           fin_flag = False, seq_number = 1, ack_number = 1, size = CONTROL_PACKET_SIZE),
    # Data
    Packet('F14', flow, host_1, host_2, syn_flag = False, ack_flag = True,
           fin_flag = False, seq_number = 1, ack_number = 1, size = DATA_PACKET_SIZE),
]
print([str(p) for p in p2.packets])
print([str(p) for p in p2_expect])
assert p2.packets == p2_expect


# Packets sent by host 2
p1_expect = [
    # SYN+ACK
    Packet('F12', flow, host_2, host_1, syn_flag = True, ack_flag = True,
           fin_flag = False, seq_number = 0, ack_number = 1, size = CONTROL_PACKET_SIZE),
    # Data ACK
    Packet('F15', flow, host_2, host_1, syn_flag = False, ack_flag = True,
           fin_flag = False, seq_number = 1, ack_number = 2, size = CONTROL_PACKET_SIZE)
]
print([str(p) for p in p1.packets])
print([str(p) for p in p1_expect])
assert p1.packets == p1_expect
