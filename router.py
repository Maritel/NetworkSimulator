from queue import PriorityQueue
from host import Host
from packet import Packet, LinkStatePacket

class Router(object):
    def __init__(self, event_manager, i, table=None, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        self.table = table if table != None else {}  # dict of destHost -> nextRouter
        self.links = []  # links that this router can access
        self.debug = debug
        # network defined as dict (key, value) = (router, [(router, cost, link)])
        self.network = {self: []}

    def __hash__(self):
        return hash(self.i)

    def __eq__(self, other):
        return self.i == other.i

    def __lt__(self, other):
        return True
    
    def __gt__(self, other):
        return False
    
    def add_link(self, link):
        self.links.append(link)
        self.network[self].append((link.dest, link.delay + link.buffer_usage/link.rate, link))
        # update table
        # if contains host then set to host, otherwise copy over new settings
        if type(link.dest) is Host:
            self.table[link.dest] = link
        else:
            for dest in link.dest.table:
                self.table[dest] = link
            
    def on_reception(self, t, p):
        if self.debug:
            print("t={}: {}: {} packet received: {}".
                  format(round(t, 6), self.i, type(p), p))
        if type(p) is LinkStatePacket:
            if(p.sender in self.network and set(p.data) == set(self.network[p.sender])):
                return 
            self.network[p.sender] = p.data
            print("changed")

            self.update_table()
            
            try:
                for nextLink in self.links:
                    nextLink.on_packet_entry(t, p)
            except:
                #silently fail
                return False
        else:
            print("route reg packet")
            try:
                nextLink = self.table[p.receiver]
                nextLink.on_packet_entry(t, p)
            except:
                print("routing failed, probably b/c not in table")

            print("routed succesfully")
        
    def update_table(self):
        # network defined as dict (key, value) = (router, [(router, cost, link)])
        N = len(self.network)
        dist = {self: 0} #not in dist = inf
        child = {self: []} #children of certain router
        vis = {self}
        pq = PriorityQueue() #holds (dist, (start, end, link))
        assert(pq.empty())

        for router in self.network[self]:
            pq.put((router[1], (self, router[0], router[2])))
            vis.add(router[0])

        while not pq.empty():
            top = pq.get()
            dist[top[1][1]] = top[0]
            if(top[1][0] in child):
                child[top[1][0]].append((top[1][1], top[1][2]))
            else:
                child[top[1][0]] = [(top[1][1], top[1][2])]
            if top[1][1] in self.network:
                for router in self.network[top[1][1]]:
                    if(type(top[1][1]) is Router and router[0] not in vis):
                        pq.put((top[0] + router[1],
                                (top[1][1], router[0], router[2])))
                        vis.add(router[0])

        #shortest distance information acquired
        """
        print("router start {}".format(self.i))
        for rr in child:
            print(rr.i, [x[0].i for x in child[rr]])
        """
        seen = set([])
        
        def dfsUpdate(n, base):
            if(n not in child):
                return
            for i in child[n]:
                if i[0] not in seen:
                    seen.add(i[0])
                    self.table[i[0]] = base
                    dfsUpdate(i[0], base)

        for nxtRt in child[self]:
            self.table[nxtRt[0]] = nxtRt[1]
            dfsUpdate(nxtRt[0], nxtRt[1])

