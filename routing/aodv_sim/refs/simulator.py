from aodv_client import Client
import threading
import select
import socket
class Simulator(threading.Thread):
    def __init__(
            self, node_pos, address_list,
            latency_factor = 10
    ):
        threading.Thread.__init__(self)
        self.node_pos = node_pos
        self.address_list = address_list
        self.nodes = [
            Client(address) for address in address_list
        ]
        self.listener_port = [
            1000 + 100 * i for i in range(len(self.nodes))
        ]
        self.aodv_listener_port = [
            2000 + 100 * i for i in range(len(self.nodes))
        ]
        for i in range(len(self.nodes)):
            self.nodes[i].listener_port = self.aodv_listener_port[i]
            self.nodes[i].simulator_listener_port = self.listener_port[i]


        # self.nodes_list = nodes
        # self.nodes_port = [
        #     1000 + 100 * i for i in range(len(nodes))
        # ]
        self.latency_factor = latency_factor

    def broadcast_message(
            self, src_node, message: bytes
    ):
        pass

    def compute_distance(
            self, node1, node2
    ):
        # use node.position (x, y) to compute distance
        diff_x = node1.position[0] - node2.position[0]
        diff_y = node1.position[1] - node2.position[1]
        return (diff_x ** 2 + diff_y ** 2) ** 0.5

    def compute_latency(self, node1, node2):
        distance = self.compute_distance(node1, node2)
        # assume 1m/s
        return distance * self.latency_factor

    def run(self):
        self.socket_list = []
        for i in range(len(self.nodes)):
            listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener_sock.bind(('localhost', self.listener_port[i]))
            listener_sock.setblocking(False)

            self.socket_list.append(listener_sock)
        for i in range(len(self.nodes)):
            self.nodes[i].start()
        while True:
            readables, _, _ = select.select(self.socket_list, [], [])
            for readable in readables:
                message, address = readable.recvfrom(1024)
                print(message, address)
                a = 1




if __name__ == '__main__':
    node_pos = [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1)
    ]
    address_list = [
        bytes([i]) for i in range(len(node_pos))
    ]
    simulator_inst = Simulator(node_pos, address_list)
    simulator_inst.start()