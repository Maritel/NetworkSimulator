from queue import PriorityQueue
from host import Host
from packet import Packet, LinkStatePacket

class Router(object):
    def __init__(self, event_manager, i, table=None, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        self.table = table if table != None else {}  # dict of destID -> nextID
        self.links = []  # links that this router can access
        self.debug = debug
        # network defined as dict (key, value) = (router, [(router, cost)])
        self.network = {i: []}

    def add_link(self, link):
        print("link", link.i)
        self.links.append(link)
        self.network[self.i].append((link.dest, link.delay + link.buffer_usage/link.rate))
        # update table
        # if contains host then set to host, otherwise copy over new settings
        if type(link.dest) is Host:
            self.table[link.dest.i] = link.i
        else:
            for dest in link.dest.table:
                self.table[dest] = link.i
        print("id", self.i, "table", self.table)
            
    def on_reception(self, t, p):
        if self.debug:
            print("t={}: {}: packet received: {}".
                  format(round(t, 6), self.i, p))
        if type(p) is LinkStatePacket:
            if(p.data == self.network[p.sender]):
                return
            self.network[p.sender] = p.data
            self.update_table()
            try:
                for nextLink in self.links:
                    nextLink.on_packet_entry(t, p)
            except:
                #silently fail
                return False
        else:
            try:
                nextLink = self.links[self.table[p.receiver.i]]
                nextLink.on_packet_entry(t, p)
            except:
                #silently fail
                return False
        
    def update_table(self):
        N = len(self.network)
        dist = {self.i: 0} #not in dist = inf
        child = {self.i: []} #store self as -1 for termination
        vis = {self.i}
        pq = PriorityQueue() #holds (dist, (start, end))
        assert(pq.empty())

        for router in self.network[self.i]:
            pq.put((router[1], (self.i, router[0])))

        while not pq.empty():
            top = pq.get()
            dist[top[1][1]] = top[0]
            if(top[1][0] in child):
                child[top[1][0]].append(top[1][1])
            else:
                child[top[1][0]] = [top[1][1]]
            for router in self.network[top[1][1]]:
                if(router[0] not in vis):
                    pq.put((top[0] + router[1],
                            (top[1][1], router[0])))
                    vis.add(router[0])

        #shortest distance information acquired

        def dfsUpdate(n, base):
            if(n not in child):
                return
            for i in child[n]:
                self.table[i] = base
                dfsUpdate(i, base)

        for nxtRt in child[self.i]:
            dfsUpdate(nxtRt, nxtRt)

