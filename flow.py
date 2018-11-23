from events import FlowAckTimeout, HandshakeRetry
from packet import Packet


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

        # 'Handshake status' is the highest-numbered handshake packet received
        # by either source or destination.
        # -1: SRC hasn't sent Syn.
        # 0: SRC has sent Syn.
        # 1: DST has received Syn and sent SynAck.
        # 2: SRC has received SynAck and sent Ack.
        # 3: DST has received Ack.
        self.handshake_status = -1
        self.handshake_n_steps = 3
        self.handshake_base_wait_time = 0.1  # in seconds; doubles on failure

        # number of times handshaking was tried at this level
        self.handshake_source_n_tries = 0
        self.handshake_destination_n_tries = 0

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

    def is_handshake_done(self):
        return self.handshake_status == 3

    def perform_handshake(self, t, level):
        if level == 1:
            # Source needs to send Syn.
            if self.handshake_status >= 2:
                return  # SRC received SynAck so nothing happens.
            p = self.make_packet(packet_type='h1')
            self.source.link.on_packet_entry(t, p)
            if self.debug:
                print("t={}, Flow {}, {} sends handshake packet {}".
                      format(t, self, self.source, p))

            # Specify a time to try this again.
            wait_time = self.handshake_base_wait_time * \
                        2 ** self.handshake_source_n_tries
            self.handshake_source_n_tries += 1
            self.em.enqueue(HandshakeRetry(t, flow=self, level=level))
        elif level == 2:
            # Destination needs to send SynAck.
            if self.handshake_status >= 3:
                return  # DST received Ack so nothing happens.
            p = self.make_packet(packet_type='h2')
            self.destination.link.on_packet_entry(t, p)
            if self.debug:
                print("t={}, Flow {}, {} sends handshake packet {}".
                      format(t, self, self.destination, p))

            # Specify a time to try this again.
            wait_time = self.handshake_base_wait_time * \
                        2 ** self.handshake_destination_n_tries
            self.handshake_destination_n_tries += 1
            self.em.enqueue(HandshakeRetry(t, flow=self, level=level))
        else:  # level = 3
            # SRC needs to send Ack.
            p = self.make_packet(packet_type='h3')
            self.source.link.on_packet_entry(t, p)

            if self.debug:
                print("t={}: Flow {}, {} sends handshake packet {}".
                      format(t, self, self.source, p))

            # Specify at ime to try this again
            wait_time = self.handshake_base_wait_time * \
                        2 ** self.handshake_source_n_tries
            self.handshake_source_n_tries += 1
            self.em.enqueue(HandshakeRetry(t, flow=self, level=level))

    def consider_send(self, t):
        if self.amount_left > 0 and \
                        len(self.outstanding_packets) < self.window_size:

            # If handshake status is 0, 1, 2, we don't do anything.
            if self.handshake_status == -1:
                self.perform_handshake(t, 1)
            elif self.is_handshake_done():
                # SRC can send freely now

                p = self.make_packet(packet_type='data')

                self.outstanding_packets.add(p)

                if self.debug:
                    print("t={}, {} sends packet {}".
                          format(round(t, 6), self.i, p))

                self.em.enqueue(FlowAckTimeout(t + self.ack_wait_time, self, p))
                self.source.link.on_packet_entry(t, p)
                self.consider_send(t)  # Send as much as possible.

    def on_source_reception(self, t, p):
        if p.packet_type == 'ack' and self.is_handshake_done():
            acked_packet = p.info
            if acked_packet in self.outstanding_packets:
                self.outstanding_packets.remove(acked_packet)
                self.amount_left -= acked_packet.size
                self.consider_send(t)
        elif p.packet_type == 'h2':
            self.handshake_status = max(self.handshake_status, 2)
            self.perform_handshake(t, level=3)
        else:
            assert False

    def on_destination_reception(self, t, p):
        if p.packet_type == 'data' and self.is_handshake_done():
            ack_packet = self.make_packet(packet_type='ack')
            if self.debug:
                print("t={}: {}: creating ack packet: {}".
                      format(round(t, 6), self.i, ack_packet))
            self.destination.link.on_packet_entry(t, ack_packet)
        elif p.packet_type == 'h1':
            self.handshake_status = max(self.handshake_status, 1)
            self.perform_handshake(t, level=2)
        elif p.packet_type == 'h3':
            self.handshake_status = max(self.handshake_status, 3)
        else:
            assert False

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

    def __str__(self):
        return self.i
