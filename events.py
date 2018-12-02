from abc import ABC, abstractmethod
import queue
import datetime
import time
from packet import LinkStatePacket

class Event(ABC):
    def __init__(self, t):
        self.t = t
        self.valid = True

    def is_valid(self):
        return self.valid

    def invalidate(self):
        self.valid = False

    @abstractmethod
    def run(self):
        """Do what the event is supposed to do"""
        pass

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


class SendLinkState(Event):
    def __init__(self, t):
        super().__init__(t)
    
    def run(self):
        pass

class EventManager(object):
    def __init__(self, logging=True, max_time=300):
        self.event_queue = queue.PriorityQueue()
        self.current_time = 0
        self.max_time = max_time
        self.logging = logging
        self.initialize_log()
        self.router_list = {}
        self.flowends = set()  # Set of flowends left

    def enqueue(self, event):
        self.event_queue.put(event)

    def register_flowend(self, flowend):
        self.flowends.add(flowend)
        print('Flowend registered:', flowend, 'Set:', list(str(x) for x in self.flowends))
    
    def flowend_done(self, flowend):
        self.flowends.remove(flowend)
        print('Flowend removed:', flowend, 'Set:', list(str(x) for x in self.flowends))

    def run(self, interval=5):
        print(self.router_list)
        for router in self.router_list:
            print([x.i for x in self.router_list[router].links])

        self.enqueue(SendLinkState(0.0))
        # Trick: if linkstate is the only event, do nothing
            
        while not self.event_queue.empty() and self.flowends and self.current_time <= self.max_time:
            ev = self.event_queue.get()
            self.current_time = ev.t
            if type(ev) is SendLinkState:
                self.enqueue(SendLinkState(ev.t + interval))
                for router in self.router_list:
                    payload = []
                    for link in self.router_list[router].links:
                        payload.append((link.dest, link.delay + (link.interval_usage/interval)/link.rate, link))
                        link.interval_usage = 0
                    p = LinkStatePacket("ptmp", self.router_list[router], payload)
                    for link in self.router_list[router].links:
                        link.on_packet_entry(self.current_time, p)
            elif ev.is_valid():
                ev.run()

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
