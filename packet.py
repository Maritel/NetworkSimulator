DATA_PACKET_SIZE = 8192
CONTROL_PACKET_SIZE = 512


class Packet(object):
    # TYPES OF PACKETS:
    # 'data'
    # 'ack'
    # 'h1' - handshake 1, or Syn sent by SRC
    # 'h2' - handshake 2, or SynAck sent by DST after receiving h1 from SRC
    # 'h3' - handshake 3, or Ack sent by SRC after receiving h2 from SRC

    def __init__(self, i, flow, sender, receiver, syn_flag, ack_flag, fin_flag,
                 seq_number, ack_number, size):
        self.i = i
        self.flow = flow
        self.sender = sender
        self.receiver = receiver
        self.syn_flag = syn_flag
        self.ack_flag = ack_flag
        self.fin_flag = fin_flag
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.size = size

    def __str__(self):
        return "(id: {}, flow: {}, sender: {}, receiver: {}, syn: {}, " \
               "ack: {}, fin: {}, seq#: {}, ack#: {}, size: {})"\
            .format(self.i,
                    self.flow.i,
                    self.sender.i,
                    self.receiver.i,
                    int(self.syn_flag),
                    int(self.ack_flag),
                    int(self.fin_flag),
                    self.seq_number,
                    self.ack_number,
                    self.size)
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
