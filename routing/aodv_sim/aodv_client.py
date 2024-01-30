from routing_table import RoutingTab, routing_entry
import threading
import socket, select
import os
import time


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
        self.comm_port = client_config["comm_port"]
        self.control_port = client_config["control_port"]
        self.log_dir = client_config["log_dir"]
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = self.log_dir + "/log.txt"

    # def send_message(
    #         self, address: bytes, message: bytes
    # ):
    #     assert len(address) == 1  # one byte
    #     if address in self.routing_table.routing_dict:
    #         # send message
    #         next_hop_ip = self.routing_table.routing_dict[address].next_hop
    #         self.send_implementation(next_hop_ip, bytes([0]) + message)
    #     else:
    #         # send RREQ
    #         pass
    #
    # # Only for simulation, the implementation with LoRa should be different
    # def send_implementation(self, address: bytes, message: bytes):
    #     self.aodv_listener_sock.sendto(message, 0, ('localhost', self.communication_port))
    #

    def _to_log(self, log_content: str):
        time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
        with open(self.log_file, 'a') as f:
            f.write("[{}]:\t".format(time_stamp))
            f.write(log_content)

    def run(self):
        self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_sock.bind(('localhost', self.comm_port))
        self.listener_sock.setblocking(False)

        self.aodv_listener_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.aodv_listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.aodv_listener_sock.bind(('localhost', self.control_port))
        self.aodv_listener_sock.setblocking(False)

        self._to_log("Start listening on port: " + str(self.comm_port) + "\n")
        self._to_log("Start listening on port: " + str(self.control_port) + "\n")
        self._to_log("Successfully start the client.\n")
        while True:
            a = 1
