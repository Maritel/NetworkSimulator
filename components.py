class Host(object):
    def __init__(self, i):
        self.i = i

class Router(object):
    def __init__(self, i):
        self.i = i
        # Routing table for routers
        self.table = table

class Link(object):
    def __init__(self, i, rate, delay, buffer_size):
        self.i = i
        self.rate = rate # bits per second
        self.delay = delay # seconds
        self.buffer_size = buffer_size # bits

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
