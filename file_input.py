from components import *
import json

def read_network(filename, event_manager):
    """
    Create a network from input file.
    Add initial events to the event manager.
    """

    with open(filename) as f:
        j = json.load(f)
    
    endpts = {}  # Map of endpoint id -> endpoint
    hosts = {}
    routers = {}
    links = {}
    flows = {}

    for h in j.get('hosts', []):
        i = h['id']
        assert i not in endpts, 'Endpoint with id %s already exists' % i
        host = Host(event_manager, i)
        endpts[i] = host
        hosts[i] = host
    for r in j.get('routers', []):
        i = r['id']
        assert i not in endpts, 'Endpoint with id %s already exists' % i
        router = Router(event_manager, i)
        endpts[i] = router
        routers[i] = router
    for l in j.get('links', []):
        i = l['id']
        end_a = endpts[l['end_a']]
        end_b = endpts[l['end_b']]
        assert end_a != end_b, 'Loop link'
        i_a = i + '_a'
        i_b = i + '_b'
        link_a = Link(event_manager, i_a, end_a, end_b, l['rate'], l['delay'],
                      l['buffer_size'])
        end_a.add_link(link_a)
        links[i_a] = link_a
        link_b = Link(event_manager, i_b, end_b, end_a, l['rate'], l['delay'],
                      l['buffer_size'])
        end_b.add_link(link_b)
        links[i_b] = link_b

    for json_flow in j.get('flows', []):
        source = endpts[json_flow['source']]
        assert isinstance(source, Host), \
               'Source %s is not a host' % json_flow['source']
        destination = endpts[json_flow['destination']]
        assert isinstance(destination, Host), \
               'Destination %s is not a host' % json_flow['destination']
        flow = Flow(event_manager,
                    json_flow['id'],
                    source,
                    destination,
                    json_flow['amount']) # amount of data in bits
        flows[flow.i] = flow
        # For a flow that starts after 'delay', we add a FlowConsiderSend
        # event at time 'delay'
        event_manager.enqueue(FlowConsiderSend(json_flow['start_delay'], flow))

    return hosts, routers, links, flows



