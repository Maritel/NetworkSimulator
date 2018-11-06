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
    for h in j.get('hosts', []):
        i = h['id']
        endpts[i] = Host(event_manager, i)
    for r in j.get('routers', []):
        i = r['id']
        endpts[i] = Router(event_manager, i)
    for l in j.get('links', []):
        i = l['id']
        end_a = endpts[l['end_a']]
        end_b = endpts[l['end_b']]
        link = Link(event_manager, i, end_a, end_b, l['rate'], l['delay'],
                    l['buffer_size'])
        end_a.add_link(link)
        end_b.add_link(link)

    for json_flow in j.get('flows', []):
        source = endpts[json_flow['source']]
        assert isinstance(source, Host)
        destination = endpts[json_flow['destination']]
        assert isinstance(destination, Host)
        flow = Flow(event_manager,
                    json_flow['id'],
                    source,
                    destination,
                    json_flow['amount']) # amount of data in bits
        # For a flow that starts after 'delay', we add a FlowConsiderSend
        # event at time 'delay'
        event_manager.enqueue(FlowConsiderSend(json_flow['start_delay'], flow))



