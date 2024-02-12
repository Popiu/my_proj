class routing_entry:
    def __init__(
            self, target_seq, hop_count,
            next_hop, list_of_prev_hop,
            lifetime
    ):
        self.target_seq = target_seq
        self.hop_count = hop_count
        self.next_hop = next_hop
        self.list_of_prev_hop = list_of_prev_hop
        self.lifetime = lifetime


class RoutingTab:
    def __init__(self):
        self.routing_dict = {}
