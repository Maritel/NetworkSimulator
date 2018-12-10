from congestion_control import StopAndWait
from events import Event
from packet import Packet, DATA_PACKET_SIZE, CONTROL_PACKET_SIZE
from math import ceil

# https://tools.ietf.org/html/rfc793#section-3.4


class FlowEnd(object):
    def __init__(self, event_manager, i, flow, host, other_host, amount, cc,
                 debug=True):
        self.debug = debug
        self.em = event_manager
        self.i = i
        self.flow = flow
        self.host = host
        self.other_host = other_host


        #
        # STATE VARIABLES
        #

        # There are a lot of two TCP states, but we only care if the Syn
        # packet (the one with seq# send_iss) has been acknowledged.
        # If it has, we are established and can send and acknowledge data.
        # Otherwise, we must continue the handshake until establishment.

        self.send_iss = 0  # seq# of Syn packet that I send

        # Once this seq# is acknowledged, we're done.
        self.last_seq_number = self.send_iss + ceil(amount / DATA_PACKET_SIZE)

        # seq# of the first unacked packet, even if I haven't sent it
        self.send_first_unacked = self.send_iss

        # seq# of next packet to send, # if all outstanding packets are acked
        self.send_next = self.send_iss

        self.receive_iss = None  # seq# of Syn packet that counterparty sends

        # seq# of the first packet I haven't received
        self.receive_next = None
        self.received_seqs = set()  # Set of received sequence numbers

        # Timeouts that are relevant to me. Also remembers outstanding packets.
        # Map of (Seq # -> AckTimeout event for that Seq#)
        self.ack_timeout_events = {}

        # Congestion control algorithm.
        self.cc = cc

        # RTT sampling parameters
        # Sequence number of packet currently being sampled
        self.rtt_sample_seq = None
        # Time the packet was sent
        self.rtt_sample_send_time = None
        self.srtt = None   # Smoothed RTT
        self.rttvar = None # Variance in RTT

        #
        # OPERATION PARAMETERS
        #
        # Minimum ACK timeout permitted by RFCs is 1.0s.
        # "Whenever RTO is computed, if it is less than 1 second, then the
        # RTO SHOULD be rounded up to 1 second"
        # TODO: Compute timeouts using algorithm from book.
        self.ack_wait = 1
        self.window_size = cc.initial_cwnd()

    def is_established(self):
        return self.send_first_unacked > self.send_iss

    def attempt_rtt_sample(self, t, packet):
        if self.rtt_sample_seq == None:
            # Sample this packet
            self.rtt_sample_seq = packet.seq_number
            self.rtt_sample_send_time = t

    def on_rtt_sample(self, packet, rtt, t):
        # Update srtt and rttvar (RFC 6298)
        if self.srtt == None:
            self.srtt = rtt
            self.rttvar = rtt / 2
        else:
            self.rttvar = (1-1/4) * self.rttvar + 1/4 * abs(self.srtt - rtt)
            self.srtt = (1-1/8) * self.srtt + 1/8 * rtt
        if self.debug:
            print('RTT sample: {} on pkt = {}'.format(rtt, packet))
            print('New SRTT = {}, RTTVAR = {}'.format(self.srtt, self.rttvar))

        ### Per-flow packet round-trip delay ###
        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|RTT|{}'.format(t, self.srtt))

    def act(self, t):
        if not self.is_established():
            # Resend the initial Syn packet.
            syn_packet = \
                Packet(i=self.flow.get_packet_id(),
                       flow=self.flow,
                       sender=self.host,
                       receiver=self.other_host,
                       syn_flag=True,
                       ack_flag=False,
                       fin_flag=False,
                       seq_number=self.send_iss,
                       ack_number=None,
                       size=CONTROL_PACKET_SIZE)

            self.send_acknowledgeable_packet(t, syn_packet)

        else:  # I'm established. Send a data packet if I need to.
            if self.send_next > self.last_seq_number:
                return  # All the data is sent.
            if self.send_next - self.send_first_unacked >= self.window_size:
                return  # Window size prevents a send.

            assert self.receive_next is not None  # since ESTABLISHED

            data_packet = \
                Packet(i=self.flow.get_packet_id(),
                       flow=self.flow,
                       sender=self.host,
                       receiver=self.other_host,
                       syn_flag=False,
                       ack_flag=True,
                       fin_flag=False,
                       seq_number=self.send_next,
                       ack_number=self.receive_next,
                       size=DATA_PACKET_SIZE)

            self.send_acknowledgeable_packet(t, data_packet)

            self.act(t)  # Utilize the entire window.

    def on_ack_timeout(self, t, seq_number):
        if self.debug:
            print("t={}: {} ack timeout on seq# {}"
                  .format(round(t, 6), self, seq_number))

        # We want to retransmit the first unacknowledged packet. Usually, this
        # should be the packet with #seq_number.
        assert self.send_first_unacked <= seq_number

        # Ack timeout
        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|ACKTIMEOUT|1'.format(t))

        # ADJUST SETTINGS
        self.window_size = self.cc.ack_timeout(t)
        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|WINDOW|{}'.format(t, self.window_size))

        self.retransmit(t)

    def on_reception(self, t, received_packet):
        assert received_packet.receiver == self.host
        if self.debug:
            print("t={}: {} received packet {}"
                  .format(round(t, 6), self, received_packet))

        ### Per-flow receive rate ###
        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|RCVE|{}'.format(t, received_packet.size))

        #
        # OPERATIONS AGNOSTIC TO WHETHER WE'RE ESTABLISHED
        #

        if received_packet.ack_flag:
            # Got an ACK
            # Update window size and send_first_unacked.
            # Retransmit if needed
            if received_packet.ack_number < self.send_first_unacked:
                # TODO is this possible?
                assert False

            elif received_packet.ack_number == self.send_first_unacked:
                if received_packet.size == CONTROL_PACKET_SIZE:
                    # Only non-data packets can be dupacks
                    retransmit, self.window_size = self.cc.dupack(t)
                    self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|WINDOW|{}'.format(t, self.window_size))
                    self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|DUPACK|1'.format(t))
                    if retransmit:
                        old_next = self.send_next
                        old_window_size = self.window_size
                        # Retransmit the lost packet (which is the first unacked packet)
                        # Subtle: invalidate its old ack timeout
                        self.send_next = self.send_first_unacked
                        self.window_size = 1
                        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|WINDOW|{}'.format(t, self.window_size))
                        self.ack_timeout_events[self.send_first_unacked].invalidate()
                        self.act(t)
                        # Restore previous state
                        self.send_next = old_next
                        self.window_size = old_window_size
                        self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|WINDOW|{}'.format(t, self.window_size))
                        self.act(t)
            else:
                self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|THROUGHPUT|{}'.format(
                    t, (received_packet.ack_number - self.send_first_unacked) * DATA_PACKET_SIZE))
                self.send_first_unacked = received_packet.ack_number
                self.window_size = self.cc.posack(t)
                self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|WINDOW|{}'.format(t, self.window_size))
                self.em.log_it('FLOW|{}'.format(self.i), 'T|{}|POSACK|1'.format(t))
                if self.send_first_unacked > self.last_seq_number:
                    # All packets are acked, so this flow is done
                    self.em.flowend_done(self)

            self.clear_redundant_timeouts(received_packet.ack_number)  # clean

            if self.rtt_sample_seq is not None and \
                    received_packet.ack_number > self.rtt_sample_seq:
                # NB: The only case that self.rtt_sample_seq is None is
                # when we get an ACK without ever having sent our own packet.
                # That's when we're the destination getting a SYN+ACK.
                self.on_rtt_sample(received_packet, t - self.rtt_sample_send_time, t)
                self.rtt_sample_seq = None
                self.rtt_sample_send_time = None


        #
        # OPERATIONS DEPENDING ON WHETHER WE'RE ESTABLISHED
        #

        if not self.is_established():
            # We're always sending a Syn received_packet.
            response_packet = Packet(i=self.flow.get_packet_id(),
                                     flow=self.flow,
                                     sender=self.host,
                                     receiver=self.other_host,
                                     syn_flag=True,
                                     ack_flag=False,
                                     fin_flag=False,
                                     seq_number=self.send_iss,
                                     ack_number=None,
                                     size=CONTROL_PACKET_SIZE)
            # But we also acknowledge the packet we've received if it's Syn.
            # We don't acknowledge data packets.
            if received_packet.syn_flag:
                # Update state
                self.receive_iss = received_packet.seq_number  # syn seq#
                self.receive_next = self.receive_iss + 1
                self.send_next = self.send_iss  # Reset 'next packet' to ISS

                # Modify response packet to change it to SynAck.
                response_packet.ack_flag = True
                response_packet.ack_number = self.receive_next
            
            self.send_acknowledgeable_packet(t, response_packet)

            # Can't act, since we're not established.

        else:  # We're established. A response is required if Syn or data.
            if received_packet.syn_flag or received_packet.size >= 513:
                if received_packet.syn_flag:  # Set initial sequence number
                    self.receive_iss = received_packet.seq_number
                    self.receive_next = self.receive_iss
                # Update receive_next
                self.received_seqs.add(received_packet.seq_number)
                while self.receive_next in self.received_seqs:
                    self.receive_next += 1

                response_packet = \
                    Packet(i=self.flow.get_packet_id(),
                           flow=self.flow,
                           sender=self.host,
                           receiver=self.other_host,
                           syn_flag=False,
                           ack_flag=True,
                           fin_flag=False,
                           seq_number=self.send_next,
                           ack_number=self.receive_next,
                           size=CONTROL_PACKET_SIZE)

                # Do NOT schedule a timeout, just send the packet.
                self.send(t, response_packet)

                if self.debug:
                    print("t={}: {} sends packet: {}"
                          .format(round(t, 6), self, response_packet))

            self.act(t)  # May want to send data here.

    def retransmit(self, t):
        """Assuming the window size has been set correctly, retransmit from the
        first unacknowledged packet."""
        self.send_next = self.send_first_unacked
        
        # Clear all ack timeout events, because we're starting from the first
        # unacknowledged packet anyway.
        for _, event in self.ack_timeout_events.items():
            event.invalidate()
        self.ack_timeout_events.clear()

        self.act(t)


    def send_acknowledgeable_packet(self, t, p):
        """Send an acknowledgeable packet. Update state such as send_next."""
        if p.seq_number != self.send_next:
            print(p, self.send_next)
            assert False

        # Schedule an AckTimeout
        ack_timeout_event = AckTimeout(t + self.ack_wait, self, self.send_next)
        self.ack_timeout_events[self.send_next] = ack_timeout_event
        self.em.enqueue(ack_timeout_event)

        # RTT sampling
        self.attempt_rtt_sample(t, p)

        # Update internal state.
        self.send_next += 1

        if self.debug:
            print("t={}: {} sends packet: {}".format(round(t, 6), self, p))

        # Send the packet.
        self.send(t, p)

    def send(self, t, p):
        # Send without acknowledgement processing.
        self.host.send_packet(t, p)
        # update event manager count b/c no packet enqueue
        ### Per-flow send rate ###
        self.em.log_it('FLOW|{}'.format(self.i),
                       'T|{}|SEND|{}'.format(t, p.size))

    def clear_redundant_timeouts(self, first_unacked_number):
        invalidated_seq_numbers = []
        for seq_number, event in self.ack_timeout_events.items():
            if seq_number < first_unacked_number:
                event.invalidate()
                invalidated_seq_numbers.append(seq_number)

        for seq_number in invalidated_seq_numbers:
            self.ack_timeout_events.pop(seq_number, None)

    def __str__(self):
        return "{}/{}".format(self.i, self.host.i)

    def __eq__(self, other):
        return self.i == other.i if isinstance(other, FlowEnd) else False

    def __hash__(self):
        return hash(self.i)


class FlowEndAct(Event):
    def __init__(self, t, flow_end):
        super().__init__(t)
        self.flow_end = flow_end  # flow which starts

    def run(self):
        self.flow_end.act(self.t)


class AckTimeout(Event):
    def __init__(self, t, flow_end, seq_number):
        super().__init__(t)
        self.flow_end = flow_end  # either FlowSrc or FlowDst
        self.seq_number = seq_number
    
    def run(self):
        self.flow_end.on_ack_timeout(self.t, self.seq_number)


class Flow(object):
    def __init__(self, event_manager, i, src_host, dst_host, amount,
                 start_delay, src_cc, debug=True):
        self.debug = debug
        self.em = event_manager
        self.i = i
        self.src_host = src_host  # a Host
        self.dst_host = dst_host  # a Host
        self.amount = amount
        self.start_delay = start_delay

        self.src = FlowEnd(event_manager=self.em,
                           i=i + 'SRC',
                           flow=self,
                           host=self.src_host,
                           other_host=self.dst_host,
                           amount=self.amount,
                           cc=src_cc,
                           debug=self.debug)

        self.dst = FlowEnd(event_manager=self.em,
                           i=i + 'DST',
                           flow=self,
                           host=self.dst_host,
                           other_host=self.src_host,
                           amount=0,
                           cc=StopAndWait(),
                           debug=self.debug)

        self.em.register_flowend(self.src)
        self.em.register_flowend(self.dst)
        self.em.enqueue(FlowEndAct(t=self.start_delay, flow_end=self.src))

        self.counter = 0

    def get_counter(self):
        # Generates unique ids.
        self.counter += 1
        return self.counter

    def get_packet_id(self):
        # Generates unique packet ids. Debugging purposes only.
        return self.i + str(self.get_counter())

    def __eq__(self, other):
        return self.i == other.i if isinstance(other, Flow) else False

    def __hash__(self):
        return hash(self.i)
