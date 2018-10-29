class Host(object):
    def __init__(self, i):
        self.i = i

class Router(object):
    def __init__(self, i):
        self.i = i
        # Routing table for routers
        self.table = table

class Link(object):
    def __init__(self, i, end1, end2, rate, delay, buf_size):
        self.i = i
        # Routers and hosts
        self.end1 = end1
        self.end2 = end2
        self.rate = rate # bits per second
        self.delay = delay # seconds
        self.buf_size = buf_size # bits

class Flow(object):
    def __init__(self, i, source, destination, amount):
        self.i = i
        self.source = source
        self.destination = destination
        self.amount = amount # bits

class Packet(object):
    def __init__(self, i, message_type, size):
        self.i = i
        self.message_type = message_type
        self.size = size # bits

