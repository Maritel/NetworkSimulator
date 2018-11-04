import queue

class Event(object):
    # useful class
    pass


class FlowConsiderSend(Event):
    def __init__(self, t, flow):
        self.t = t
        self.flow = flow  # flow which starts


class FlowAckTimeout(Event):
    def __init__(self, t, flow, packet):
        self.t = t
        self.flow = flow
        self.packet = packet  # which packet this timeout refers to


class LinkEntry(Event):
    def __init__(self, t, link, packet):
        self.t = t
        self.link = link
        self.packet = packet


class LinkBufferRelease(Event):
    # When a packet is released from the link's buffer.
    def __init__(self, t, link):
        self.t = t
        self.link = link


class LinkExit(Event):
    # When a packet reaches the end of a link.
    def __init__(self, t, link, exit_end, packet):
        self.t = t
        self.link = link
        self.exit_end = exit_end  # 0 or 1
        self.packet = packet


class EventManager(object):
    def __init__(self):
        self.event_queue = queue.PriorityQueue()
        self.current_time = 0

    def enqueue(self, event):
        self.event_queue.put((event.t, event))

    def run(self):
        while not self.event_queue.empty():
            t, event = self.event_queue.get()
            self.current_time = t

            if type(event) is FlowConsiderSend:
                event.flow.consider_send(t)
            elif type(event) is FlowAckTimeout:
                event.flow.on_ack_timeout(event.t, event.packet)
            elif type(event) is LinkExit:
                event.link.on_packet_exit(event.t, event.exit_end, event.packet)
            else:
                pass
