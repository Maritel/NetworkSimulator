from file_input import read_network
from events import EventManager

em = EventManager()
hosts, routers, links, flows = read_network('test_case_0.json', em)
assert list(hosts.keys()) == ['H1', 'H2']
assert hosts['H1'].link == links['L1_a']
assert hosts['H2'].link == links['L1_b']
assert routers == {}
assert list(links.keys()) == ['L1_a', 'L1_b']
assert links['L1_a'].source == hosts['H1']
assert links['L1_a'].dest == hosts['H2']
assert links['L1_a'].rate == 10e6
assert links['L1_a'].delay == 10e-3
assert links['L1_a'].buffer_capacity == 64e3
assert links['L1_b'].source == hosts['H2']
assert links['L1_b'].dest == hosts['H1']
assert links['L1_b'].rate == 10e6
assert links['L1_b'].delay == 10e-3
assert links['L1_b'].buffer_capacity == 64e3
assert list(flows.keys()) == ['F1']
assert flows['F1'].source == hosts['H1']
assert flows['F1'].destination == hosts['H2']
assert flows['F1'].amount_left == 1.6e8
