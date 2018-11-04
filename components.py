class Host(object):
    def __init__(self, i):
        self.i = i  # string ID; unique for all components
        self.link = None  # link that this host can access


class Router(object):
    def __init__(self, i, table=None):
        self.i = i  # string ID; unique for all components
        # Routing table for routers
        self.table = table  # dict(ID -> ID)
        self.links = []  # links that this router can access


class Link(object):
    def __init__(self, i, end_a, end_b, rate, delay, buf_size):
        self.i = i
        self.ends = (end_a, end_b)  # Each end is either a router or a host
        self.rate = rate  # bits per second
        self.delay = delay  # seconds
        self.buf_size = buf_size  # bits


class Flow(object):
    def __init__(self, i, source, destination, amount):
        self.i = i
        self.source = source
        self.destination = destination
        self.amount = amount  # bits


class Packet(object):
    def __init__(self, i, source, destination, message_type, size):
        self.i = i
        self.source = source
        self.destination = destination
        self.message_type = message_type
        self.size = size # bits

