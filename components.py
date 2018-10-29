class Host(object):
    def __init__(self):
        pass

class Router(object):
    def __init__(self):
        pass

class Link(object):
    def __init__(self, capacity, constant_delay, buffer_size):
        self.capacity = capacity
        self.constant_delay = constant_delay
        self.buffer_size = buffer_size

class Flow(object):
    def __init__(self):
        pass

class Packet(object):
    def __init__(self):
        pass
