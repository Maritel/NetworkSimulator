from components import *
from events import *
from file_input import read_network

if __name__ == '__main__':
    em = EventManager()
    read_network('test_case_0.json', em)

    # host_1 = Host(em, 'H1', debug=False)
    # host_2 = Host(em, 'H2', debug=False)
    # link = Link(em, 'L1', host_1, host_2, 10485760, 0.01, 524288, debug=False)
    # host_1.link = link
    # host_2.link = link
    # flow = Flow(em, 'F1', host_1, host_2, 8 * 20 * 1024 * 1024, debug=False)
    # em.enqueue(FlowConsiderSend(0, flow))
    
    em.run()
    print(em.current_time)



