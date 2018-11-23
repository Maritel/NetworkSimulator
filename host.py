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
        if self.debug:
            print("t={}: {}: packet received: {}".
                  format(round(t, 6), self.i, p))

        assert p.destination == self
        assert p.flow.source == self or p.flow.destination == self

        if p.flow.source == self:
            p.flow.on_source_reception(t, p)
        else:
            p.flow.on_destination_reception(t, p)

    def __str__(self):
        return self.i