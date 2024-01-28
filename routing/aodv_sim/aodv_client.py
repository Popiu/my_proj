from routing_table import RoutingTab, routing_entry
import threading
import socket, select

# protocol type
# 0: regular
# 1: RREQ
# 2: RREP
# 3: RERR


class Client(threading.Thread):
    def __init__(
            self, address: bytes, client_config: dict
    ):
        threading.Thread.__init__(self)
        assert len(address) == 1  # one byte
        self.address = address
        self.routing_table = RoutingTab()

        # Only for simulation
        self.client_config = client_config
        self.communication_port = client_config["communication_port"]
        self.controller_port = client_config["controller_port"]

    def send_message(
            self, address: bytes, message: bytes
    ):
        assert len(address) == 1  # one byte
        if address in self.routing_table.routing_dict:
            # send message
            next_hop_ip = self.routing_table.routing_dict[address].next_hop
            self.send_implementation(next_hop_ip, bytes([0]) + message)
        else:
            # send RREQ
            pass

    # Only for simulation, the implementation with LoRa should be different
    def send_implementation(self, address: bytes, message: bytes):
        self.aodv_listener_sock.sendto(message, 0, ('localhost', self.communication_port))

    def run(self):
        self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_sock.bind(('localhost', self.communication_port))
        self.listener_sock.setblocking(False)


        self.aodv_listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.aodv_listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.aodv_listener_sock.bind(('localhost', self.controller_port))
        self.aodv_listener_sock.setblocking(False)


        while True:
            # receive message
            self.aodv_listener_sock.sendto("Hello".encode("utf-8"), 0, ('localhost', self.communication_port))
