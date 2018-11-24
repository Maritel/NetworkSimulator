from packet import Packet


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

        assert p.receiver == self
        assert p.flow.src_host == self or p.flow.dst_host == self

        if p.flow.src_host == self:
            p.flow.src.on_reception(t, p)
        else:
            p.flow.dst.on_reception(t, p)

    def __str__(self):
        return self.i