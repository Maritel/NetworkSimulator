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
    def __init__(self, logging=True):
        self.event_queue = queue.PriorityQueue()
        self.current_time = 0
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

    def run(self, stop_when_flows_done=True, max_time=None, interval=5):
        """
        Run network simulation.

        stop_when_flows_done and max_time control stopping conditions.
        We always stop when there are no more events.
        stop_when_flows_done: if True, we also stop when all flows are done.
        max_time: if not None, stop after that many seconds.
        """
        print(self.router_list)
        for router in self.router_list:
            print([x.i for x in self.router_list[router].links])

        if self.router_list:  # Only send link state if there are routers
            self.enqueue(SendLinkState(0.0))

        while not self.event_queue.empty() \
                and (not(stop_when_flows_done) or self.flowends) \
                and (max_time is None or self.current_time <= max_time):
            ev = self.event_queue.get()
            self.current_time = ev.t
            if type(ev) is SendLinkState:
                self.enqueue(SendLinkState(ev.t + interval))
                for router in self.router_list:
                    payload = []
                    for link in self.router_list[router].links:
                        cong = link.delay + (link.interval_usage / interval) \
                               / link.rate
                        payload.append((link.dest, cong, link))
                        link.interval_usage = 0
                    p = LinkStatePacket("ptmp",
                                        self.router_list[router],
                                        payload)
                    for link in self.router_list[router].links:
                        link.on_packet_entry(self.current_time, p)
            elif ev.is_valid():
                ev.run()

    def initialize_log(self):
        if self.logging:
            log_file = 'log_{}.txt'.format(int(time.time()))
            self.log = open(log_file, 'w')
            print("Logging to {}".format(log_file))
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
