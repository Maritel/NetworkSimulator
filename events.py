import queue


class Event(object):
    # useful class
    pass


class FlowStart(Event):
    def __init__(self, t, flow):
        self.t = t
        self.flow = flow  # flow which starts


class FlowSendPacket(Event):
    def __init__(self, t, flow):
        self.flow = flow  # the flow that sends


class FlowAckTimeout(Event):
    def __init__(self, t, flow, packet):
        self.t = t
        self.flow = flow
        self.packet = packet  # which packet this timeout refers to


class LinkBufferRelease(Event):
    # When a packet is released from the link's buffer.
    def __init__(self, t, link):
        self.t = t
        self.link = link


class LinkExit(Event):
    # When a packet reaches the end of a link.
    def __init__(self, t, link, end, packet):
        self.t = t
        self.link = link
        self.end = end  # 0 or 1
        self.packet = packet


class EventManager(object):
    def __init__(self, starting_events):
        self.event_queue = queue.PriorityQueue()
        for event in starting_events:
            self.event_queue.put((event.t, event))
        self.current_time = 0

    def run(self):
        while not self.event_queue.empty():
            t, event = self.event_queue.get()
            self.current_time = t

            if type(event) == FlowStart:
                pass
            elif type(event) == FlowSendPacket:
                pass
            elif type(event) == FlowAckTimeout:
                pass
            elif type(event) == LinkBufferRelease:
                pass
            elif type(event) == LinkExit:
                pass
            else:
                # what?
                pass
