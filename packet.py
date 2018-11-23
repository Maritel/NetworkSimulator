

class Packet(object):
    # TYPES OF PACKETS:
    # 'data'
    # 'ack'
    # 'h1' - handshake 1, or Syn sent by SRC
    # 'h2' - handshake 2, or SynAck sent by DST after receiving h1 from SRC
    # 'h3' - handshake 3, or Ack sent by SRC after receiving h2 from SRC

    def __init__(self, i, source, destination, flow, packet_type, size,
                 info=None, debug=True):
        self.i = i
        self.source = source
        self.destination = destination
        self.flow = flow
        self.packet_type = packet_type
        self.size = size  # bits
        self.info = info
        self.debug = debug

    def __str__(self):
        return "(id: {}, src: {}, dst: {}, " \
               "flow: {}, type: {}, " \
               "size: {})".format(self.i, self.source.i, self.destination.i,
                                  self.flow.i, self.packet_type, self.size)
