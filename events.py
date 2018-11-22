import queue

class Event(object):

    def __init__(self, t):
        # If this gets called for any reason that would be strange.
        self.t = t

    def __eq__(self, other_event):
        return self.t == other_event.t

    def __ne__(self, other_event):
        return not (self == other_event)

    def __gt__(self, other_event):
        return self.t > other_event.t

    def __lt__(self, other_event):
        return self.t < other_event.t

    def __ge__(self, other_event):
        return self.t >= other_event.t

    def __le__(self, other_event):
        return self.t <= other_event.t


class FlowConsiderSend(Event):
    def __init__(self, t, flow):
        super().__init__(t)
        self.flow = flow  # flow which starts


class FlowAckTimeout(Event):
    def __init__(self, t, flow, packet):
        super().__init__(t)
        self.flow = flow
        self.packet = packet  # which packet this timeout refers to


class LinkEntry(Event):
    def __init__(self, t, link, packet):
        super().__init__(t)
        self.link = link
        self.packet = packet


class LinkBufferRelease(Event):
    # When a packet is released from the link's buffer.
    def __init__(self, t, link):
        super().__init__(t)
        self.link = link


class LinkExit(Event):
    # When a packet reaches the end of a link.
    def __init__(self, t, link, packet):
        super().__init__(t)
        self.link = link
        self.packet = packet


class EventManager(object):
    def __init__(self):
        self.event_queue = queue.PriorityQueue()
        self.current_time = 0

    def enqueue(self, event):
        self.event_queue.put(event)

    def run(self):
        while not self.event_queue.empty():
            event = self.event_queue.get()
            self.current_time = event.t

            if type(event) is FlowConsiderSend:
                event.flow.consider_send(event.t)
            elif type(event) is FlowAckTimeout:
                event.flow.on_ack_timeout(event.t, event.packet)
            elif type(event) is LinkBufferRelease:
                event.link.on_buffer_release(event.t)
            elif type(event) is LinkExit:
                event.link.on_packet_exit(event.t, event.packet)
            else:
                pass
