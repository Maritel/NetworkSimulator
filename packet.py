DATA_PACKET_SIZE = 8192
CONTROL_PACKET_SIZE = 512


class Packet(object):
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
        if isinstance(other, Packet):
            return self.i == other.i and self.flow == other.flow and \
                   self.seq_number == other.seq_number and \
                   self.ack_number == other.ack_number
        else:
            return False


class LinkStatePacket(object):
    def __init__(self, i, sender, data):
        # sender is the node that is sending the neighbor information
        # data is the neighbor information
        self.i = i
        self.sender = sender
        self.data = data
        self.size = 512 #hardcoded
        
    def __str__(self):
        return "(id: {}, sender: {}, data: {})" \
            .format(self.i, self.sender.i, self.data)
