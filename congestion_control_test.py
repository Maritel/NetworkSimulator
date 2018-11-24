from congestion_control import StopAndWait, Reno
from events import EventManager
from host import Host
from link import Link
from flow import Flow
from packet import Packet, DATA_PACKET_SIZE, CONTROL_PACKET_SIZE

class SeqNumberRecorder:
    def __init__(self, next_component):
        self.next_component = next_component
        self.seqs = set()

    def on_reception(self, t, p):
        self.seqs.add(p.seq_number)
        self.next_component.on_reception(t, p)


def consistency_test(cc):
    n_data_packets = 10000

    em = EventManager()
    host_1 = Host(em, 'H1', debug=False)
    host_2 = Host(em, 'H2', debug=False)
    sr = SeqNumberRecorder(host_2)
    l1_a = Link(em, 'L1_a', host_1, sr, DATA_PACKET_SIZE * 1000, 0.01,
                5 * DATA_PACKET_SIZE, debug=False)
    l1_b = Link(em, 'L1_b', host_2, host_1, DATA_PACKET_SIZE * 1000, 0.01,
                5 * DATA_PACKET_SIZE, debug=False)
    host_1.link = l1_a
    host_2.link = l1_b
    flow = Flow(em, 'F1', host_1, host_2, n_data_packets * DATA_PACKET_SIZE, 1,
                cc, debug=False)
    em.run()

    assert sr.seqs == set(range(n_data_packets + 1))
    # print(sr.seqs)

consistency_test(StopAndWait())
consistency_test(Reno())
