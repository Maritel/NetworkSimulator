from events import FlowAckTimeout
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

        # 0: Nothing done
        # 1: h1 (Syn) sent by SRC
        # 2: h1 received by DST and h2 (SynAck) sent by DST
        # 3: h2 received by SRC and h3 (Ack) sent by SRC
        # 4: h3 received by DST
        self.handshake_status = 0

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

    def consider_send(self, t):
        if self.amount_left > 0 and \
                        len(self.outstanding_packets) < self.window_size:

            if self.handshake_status == 0:
                p = self.make_packet(packet_type='h1')
                # TODO: Finish
                pass
            elif self.handshake_status == 1:
                # Wait for SRC to timeout on h1 or receive h2
                pass
            elif self.handshake_status == 2:
                # Wait for SRC to timeout on h2 or receive h3
                pass
            else:
                # SRC can send freely now

                p = self.make_packet(packet_type='data')

                self.outstanding_packets.add(p)

                if self.debug:
                    print("t={}, {} sends packet {}".
                          format(round(t, 6), self.i, p))

                self.em.enqueue(FlowAckTimeout(t + self.ack_wait_time, self, p))
                self.source.link.on_packet_entry(t, p)
                self.consider_send(t)  # Send as much as possible.
        else:
            # If there's outstanding packets, then either the timeout or the
            # reception of an Ack will trigger action.
            return None

    def on_source_reception(self, t, p):
        if p.packet_type == 'ack':
            acked_packet = p.info
            if acked_packet in self.outstanding_packets:
                self.outstanding_packets.remove(acked_packet)
                self.amount_left -= acked_packet.size
                self.consider_send(t)

    def on_destination_reception(self, t, p):
        pass

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
