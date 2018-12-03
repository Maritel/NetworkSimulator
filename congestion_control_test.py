from congestion_control import StopAndWait, Reno
from events import EventManager
from host import Host
from link import Link, LinkSetUsable
from flow import Flow
from packet import Packet, DATA_PACKET_SIZE, CONTROL_PACKET_SIZE

class SeqNumberRecorder:
    def __init__(self, i, next_component):
        self.i = i
        self.next_component = next_component
        self.seqs = set()

    def on_reception(self, t, p):
        self.seqs.add(p.seq_number)
        self.next_component.on_reception(t, p)


def do_test(n_data_packets, cc, add_events):
    """
    The test has 2 hosts connected by a link, and one flow.
    """
    em = EventManager(logging=False)
    host_1 = Host(em, 'H1', debug=False)
    host_2 = Host(em, 'H2', debug=False)
    sr = SeqNumberRecorder('S', host_2)
    l1_a = Link(em, 'L1_a', host_1, sr, DATA_PACKET_SIZE * 1000, 0.01,
                5 * DATA_PACKET_SIZE, debug=False)
    l1_b = Link(em, 'L1_b', host_2, host_1, DATA_PACKET_SIZE * 1000, 0.01,
                5 * DATA_PACKET_SIZE, debug=False)
    host_1.link = l1_a
    host_2.link = l1_b
    flow = Flow(em, 'F1', host_1, host_2, n_data_packets * DATA_PACKET_SIZE, 1,
                cc, debug=False)

    add_events(em, host_1, host_2, sr, l1_a, l1_b, flow)
    em.run()

    assert sr.seqs == set(range(n_data_packets + 1))
    # print('Src send first unacked', flow.src.send_first_unacked, 'Src send next', flow.src.send_next, 'Dst receive next', flow.dst.receive_next)
    assert flow.src.last_seq_number == n_data_packets
    assert flow.src.send_first_unacked == n_data_packets + 1
    assert flow.src.send_next == n_data_packets + 1
    assert flow.dst.receive_next == n_data_packets + 1

def consistency_test(cc):
    def add_events(em, host_1, host_2, sr, l1_a, l1_b, flow):
        pass
    do_test(10000, cc, add_events)


def dropped_syn_test(cc):
    def add_events(em, host_1, host_2, sr, l1_a, l1_b, flow):
        em.enqueue(LinkSetUsable(0, l1_a, False))
        em.enqueue(LinkSetUsable(2, l1_a, True))
    do_test(5, cc, add_events)


def dropped_synack_test(cc):
    def add_events(em, host_1, host_2, sr, l1_a, l1_b, flow):
        # If we make the reverse link unusable, host_2 can never send syn+ack...
        em.enqueue(LinkSetUsable(0, l1_b, False))
        em.enqueue(LinkSetUsable(2, l1_b, True))
    do_test(5, cc, add_events)


def dropped_ack_of_synack_test(cc):
    def add_events(em, host_1, host_2, sr, l1_a, l1_b, flow):
        # Break link right after host 1 sends SYN
        em.enqueue(LinkSetUsable(1 + 0.001 + 0.01 + 0.000001, l1_a, False))    
        em.enqueue(LinkSetUsable(2, l1_a, True))
    do_test(5, cc, add_events)


def dropped_data_test(cc):
    def add_events(em, host_1, host_2, sr, l1_a, l1_b, flow):
        # RTT for this connection
        rtt = (0.001 + 0.01) * 2
        em.enqueue(LinkSetUsable(1 + 5 * rtt, l1_a, False))    
        em.enqueue(LinkSetUsable(1 + 10 * rtt, l1_a, True))    
    do_test(100, cc, add_events)


for cc in [StopAndWait(), Reno()]:
    print('Consistency test for {}'.format(cc))
    consistency_test(cc)
    print('Dropped syn test for {}'.format(cc))
    dropped_syn_test(cc)
    print('Dropped synack test for {}'.format(cc))
    dropped_synack_test(cc)
    print('Dropped ack of synack test for {}'.format(cc))
    dropped_ack_of_synack_test(cc)
    print('Dropped data test for {}'.format(cc))
    dropped_data_test(cc)

