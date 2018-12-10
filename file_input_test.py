from events import EventManager
from file_input import read_network
from host import Host
from link import Link
from flow import Flow

em = EventManager(logging=False)
hosts, routers, links, flows = read_network('test_case_0_stopandwait.json', em)
h1 = Host(em, 'H1', debug=False)
h1.add_link(links['L1_a'])
h2 = Host(em, 'H2', debug=False)
h2.add_link(links['L1_b'])
print(hosts)
assert hosts == {
    'H1': h1,
    'H2': h2
}
assert routers == {}
assert links == {
    'L1_a': Link(em, 'L1_a', hosts['H1'], hosts['H2'], 1.049e7, 10e-3, 5.24e5, debug=False),
    'L1_b': Link(em, 'L1_b', hosts['H2'], hosts['H1'], 1.049e7, 10e-3, 5.24e5, debug=False)
}
# TODO check flows; it is a bit difficult
