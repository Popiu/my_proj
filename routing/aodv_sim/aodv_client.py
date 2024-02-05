from routing_table import RoutingTab, routing_entry
import threading
import socket, select
import os
import re
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
        self.routing_table = dict()
        self.seq_no = 0  # maintaining sequence number
        self.rreq_id = 0 # maintaining the rreq id
        self.rreq_id_list = {}

        # Only for simulation
        self.client_config = client_config
        self.comm_port = client_config["comm_port"]
        self.control_port = client_config["control_port"]
        self.channel_port = client_config["channel_port"]
        self.log_dir = client_config["log_dir"]
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = self.log_dir + "/log.txt"

        self._bind_ports()
    def _process_rreq_msg(self, msg):
        msg_type = msg[0]
        src_addr = msg[1]
        src_seq = msg[2]
        dst_addr = msg[3]
        dst_seq = msg[4]
        hop_cnt = msg[5]
        rreq_id = msg[6]
        self._to_log("Receive RREQ from {}".format(src_addr))

        # Discard this RREQ if we have already received this before
        if (src_addr in self.rreq_id_list.keys()):
            per_node_list = self.rreq_id_list[src_addr]
            if rreq_id in per_node_list.keys():
                self._to_log("Discard this RREQ")

        # This is a new RREQ message. Buffer it first
        if (src_addr in self.rreq_id_list.keys()):
            per_node_list = self.rreq_id_list[src_addr]
        else:
            per_node_list = dict()

        #
        # Check if we have a route to the source. If we have, see if we need
        # to update it. Specifically, update it only if:
        #
        # 1. The destination sequence number for the route is less than the
        #    originator sequence number in the packet
        # 2. The sequence numbers are equal, but the hop_count in the packet
        #    + 1 is lesser than the one in routing table
        # 3. The sequence number in the routing table is unknown
        #
        # If we don't have a route for the originator, add an entry

        if src_addr in self.routing_table.keys():
            pass
        else:
            self.routing_table[src_addr] = {
                'Destination': str(src_addr),
                'Next-Hop': str(sender),
                'Seq-No': str(orig_seq_no),
                'Hop-Count': str(hop_count),
                'Status': 'Active'
            }


    def send_message(
            self, address: bytes, message: bytes
    ):
        assert len(address) == 1  # one byte
        if address in self.routing_table.keys():
            # send message
            next_hop_ip = self.routing_table[address].next_hop
            message_content = bytes([0]) + next_hop_ip + self.address + message
            self.send_implementation(message_content)
        else:
            self.seq_no = self.seq_no + 1
            self.rreq_id = self.rreq_id + 1

            rreq_content = self.RREQ_CONTENT(address, 255)  # 255 means -1

            self.send_implementation(rreq_content)

    def RREQ_CONTENT(self, DST_ADDR: bytes, seq_no: int):
        MSG_TYPE = bytes([1])
        SRC_ADDR = self.address
        SRC_SEQ = bytes([self.seq_no])
        DST_SEQ = bytes([seq_no])
        HOP_CNT = bytes([0])
        RREQ_ID = bytes([self.rreq_id])
        return MSG_TYPE + SRC_ADDR + SRC_SEQ + DST_ADDR + DST_SEQ + HOP_CNT + RREQ_ID


    # # Only for simulation, the implementation with LoRa should be different
    def send_implementation(self, message: bytes):
        self.channel_sock.sendto(message, 0, ('localhost', self.channel_port))

    def _to_log(self, log_content: str):
        time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
        with open(self.log_file, 'a') as f:
            f.write("[{}]:\t".format(time_stamp))
            f.write(log_content)

    def _bind_ports(self):
        # kill the process that is running binding these commands, print warnings
        find_comm_process = os.popen('lsof -i:{}'.format(self.comm_port))
        find_channel_process = os.popen('lsof -i:{}'.format(self.channel_port))
        find_control_process = os.popen('lsof -i:{}'.format(self.control_port))

        comm_list = find_comm_process.readlines()
        channel_list = find_channel_process.readlines()
        control_list = find_control_process.readlines()

        if len(comm_list) != 0:
            find_values = comm_list[1].split(" ")[2]
            self._to_log(
                "Communication port is occupied by process {} , "
                "now kill it.\n".format(find_values))
            os.system("kill {}".format(find_values))

        if len(channel_list) != 0:
            find_values = channel_list[1].split(" ")[2]
            self._to_log(
                "Channel port is occupied by process {}, "
                "now kill it.\n".format(find_values))
            os.system("kill {}".format(find_values))

        if len(control_list) != 0:
            find_values = control_list[1].split(" ")[2]
            self._to_log(
                "Control port is occupied by process {}, "
                "now kill it.\n".format(find_values))
            os.system("kill {}".format(find_values))

        self.comm_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.comm_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.comm_sock.bind(('localhost', self.comm_port))
        self.comm_sock.setblocking(False)

        self.channel_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.channel_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.channel_sock.bind(('localhost', self.channel_port))
        self.channel_sock.setblocking(False)

        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.control_sock.bind(('localhost', self.control_port))
        self.control_sock.setblocking(False)

        self._to_log("Start listening on port: " + str(self.comm_port) + "\n")
        self._to_log("Start listening on port: " + str(self.channel_port) + "\n")
        self._to_log("Start listening on port: " + str(self.control_port) + "\n")

        self._to_log("Successfully start the client.\n")

    def run(self):
        # get input
        inputs = [self.control_sock, self.comm_sock]
        output = []

        while True:
            readable, _, _ = select.select(inputs, [], inputs)
            for r in readable:
                if r is self.control_sock:
                    command, _ = self.control_sock.recvfrom(100)
                    command_str = command.decode('utf-8')
                    command_list = re.split(':', command_str)
                    command_type = command_list[0]
                    if command_type == "send":
                        self._to_log("Sending command, send to {}, {}".format(command_list[1], command_list[2]))
                        self.send_message(bytes([int(command_list[1])]), command_list[2])
                elif r is self.comm_sock:
                    command, _ = self.comm_sock.recvfrom(100)
                    command_type = command[0]
                    if command_type == 1:
                        self._process_rreq_msg(command)
                    #     self.routing_table.add_routing_entry(routing_entry(command[1:]))
                    # self._to_log("Receive packet, {}".format(str(command)))