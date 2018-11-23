from queue import PriorityQueue


class Router(object):
    def __init__(self, event_manager, i, table=None, debug=True):
        self.em = event_manager
        self.i = i  # string ID; unique for all components
        # Routing table for routers
        self.table = table  # dict(ID -> ID)
        self.links = []  # links that this router can access
        self.debug = debug

    def update_table(self, network):
        """
        Actual link state not implemented yet
        network defined as dict (key, value) = (router, [(router, cost)])
        referenced by id

        updates routing table
        """
        N = len(network)
        dist = {self.i: 0} #not in dist = inf
        child = {self.i: []} #store self as -1 for termination
        vis = {self.i}
        pq = PriorityQueue() #holds (dist, (start, end))
        assert(pq.empty())

        for router in network[self.i]:
            pq.put((router[1], (self.i, router[0])))

        while not pq.empty():
            top = pq.get()
            dist[top[1][1]] = top[0]
            if(top[1][0] in child):
                child[top[1][0]].append(top[1][1])
            else:
                child[top[1][0]] = [top[1][1]]
            for router in network[top[1][1]]:
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

    def add_link(self, link):
        self.links.append(link)

    def on_packet_reception(self, t, p):
        if self.debug:
            print("t={}: {}: packet received: {}".
                  format(round(t, 6), self.i, p))
        # assume self.table is table[destID] = linkID
        # assume routing is instantaneous
        # silently fail
        nextLink = self.links[self.table[p.destination.id]]
        try:
            nextLink.on_packet_entry(t, p)
            return True
        except:
            return False