class Node:
    def __init__(self, node_id):
        self.rreq_count = 0

    def send_packet(self, packet, dest_addr):
        # send packet
        pass

    def send_rreq(self):
        # send RREQ packet
        self.rreq_count += 1
        rreq_id = self.rreq_count
        src_addr = self.node_id
        dest_addr = 'n10'
        hop_count = 0
        rreq = 'RREQ %d %s %s %d' % (rreq_id, src_addr, dest_addr, hop_count)
        self.send_packet(rreq, 'all')

    def send_rrep(self):
        # send RREP packet
        pass

    def send_rerr(self):
        # send RERR packet
        pass

if __name__ == '__main__':
    node = Node('n1')