from packet import Packet, LinkStatePacket


class Host(object):
    def __init__(self, event_manager, i, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        self.link = None  # link that this host can access
        self.debug = debug

    def add_link(self, link):
        if self.link is not None:
            raise ValueError('Link already added')
        self.link = link

    def on_reception(self, t, p):
        if type(p) is LinkStatePacket:
            return
        
        assert p.receiver == self
        # assert p.flow.src_host == self or p.flow.dst_host == self

        if p.flow.src_host == self:
            p.flow.src.on_reception(t, p)
        else:
            p.flow.dst.on_reception(t, p)

        # Per-host receive rate #
        self.em.log_it('HOST|{}'.format(self.i), 'T|{}|RCVE|{}'.
                       format(t, p.size))

    def send_packet(self, t, response_packet):
        self.link.on_packet_entry(t, response_packet)
        # Per-host send rate #
        self.em.log_it('HOST|{}'.format(self.i), 'T|{}|SEND|{}'.
                       format(t, response_packet.size))

    def __hash__(self):
        return hash(self.i)
    
    def __eq__(self, other):
        return self.i == other.i if isinstance(other, Host) else False

    def __str__(self):
        return self.i
