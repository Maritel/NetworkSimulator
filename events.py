import queue
import datetime
import time
from packet import LinkStatePacket

class Event(object):
    def __init__(self, t):
        self.t = t
        self.valid = True

    def is_valid(self):
        return self.valid

    def invalidate(self):
        self.valid = False

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


class FlowEndAct(Event):
    def __init__(self, t, flow_end):
        super().__init__(t)
        self.flow_end = flow_end  # flow which starts


class AckTimeout(Event):
    def __init__(self, t, flow_end, seq_number):
        super().__init__(t)
        self.flow_end = flow_end  # either FlowSrc or FlowDst
        self.seq_number = seq_number


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


class LinkSetUsable(Event):
    def __init__(self, t, link, usable):
        super().__init__(t)
        self.link = link
        self.usable = usable


class EventManager(object):
    def __init__(self, logging=True):
        self.event_queue = queue.PriorityQueue()
        self.current_time = 0
        self.max_time = 100000
        self.logging = logging
        self.initialize_log()
        self.type_count = {} #count the number of packet types
        self.router_list = {}

    def enqueue(self, event):
        self.event_queue.put(event)
        if type(event) is LinkEntry:
            if type(event.packet) in self.type_count:
                self.type_count[type(event.packet)] += 1
            else:
                self.type_count[type(event.packet)] = 1

    def still_running(self):
        return len(self.type_count) == 1 and list(self.type_count.keys())[0] is LinkStatePacket
            
    def run(self):
        print(self.router_list)
        for router in self.router_list:
            print([x.i for x in self.router_list[router].links])
        while not self.still_running() and\
              not self.event_queue.empty() and\
              self.current_time <= self.max_time:
            ev = self.event_queue.get()
            if type(ev) is LinkExit:
                self.type_count[type(ev.packet)] -= 1
                if self.type_count[type(ev.packet)] == 0:
                    del self.type_count[type(ev.packet)]

            self.current_time = ev.t

            if ev.is_valid():
                if type(ev) is FlowEndAct:
                    ev.flow_end.act(ev.t)
                elif type(ev) is AckTimeout:
                    ev.flow_end.on_ack_timeout(ev.t, ev.seq_number)
                elif type(ev) is LinkBufferRelease:
                    ev.link.on_buffer_release(ev.t)
                elif type(ev) is LinkExit:
                    ev.link.on_packet_exit(ev.t, ev.packet)
                elif type(ev) is LinkSetUsable:
                    ev.link.set_usable(ev.usable)
                else:
                    pass

    def initialize_log(self):
        if self.logging:
            self.log = open('log_{}.txt'.format(int(time.time())), 'w')

            curr = str(datetime.datetime.now())
            print('-' * 8, curr, '-' * 8, file=self.log)
            print('-' * 8, 'BEGIN RUN', '-' * 8, file=self.log)

    def log_it(self, component, info):
        if self.logging:
            line = '|'.join((component, info))
            print(line, file=self.log)

    def __del__(self):
        if self.logging:
            print('-' * 8, 'END RUN', '-' * 8, file=self.log)
            self.log.close()
