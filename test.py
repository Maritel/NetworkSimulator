from components import *
from events import *

if __name__ == '__main__':
    host_1 = Host('h1')
    host_2 = Host('h2')
    link = Link('l1', host_1, host_2, 10485760, 0.01, 524288)
    host_1.link = link
    host_2.link = link
    flow = Flow('f1', host_1, host_2, 8 * 20 * 1024 * 1024)

    starting_events = [FlowStart(0, flow)]
    em = EventManager(starting_events)


