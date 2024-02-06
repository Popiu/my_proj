from routing_table import RoutingTab, routing_entry
import threading
import socket, select
import os
import re
import time


# protocol type
# 0: regular
# 1: RREQ
# msg_type(1 byte) send_addr(1 byte) receiver(1 byte) rreq_id(1 byte) src_addr(1 byte) src_seq(1 byte) dst_addr(1 byte) dst_seq(1 byte) hop_cnt(1 byte)
# 2: RREP
# msg_type(1 byte) send_addr(1 byte) receiver(1 byte)
# 3: RERR


AODV_PATH_DISCOVERY_TIME    =   30
AODV_ACTIVE_ROUTE_TIMEOUT   =   300


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
        sender_addr = msg[1]
        rreq_id = msg[2]
        src_addr = msg[3]
        src_seq = msg[4]
        dst_addr = msg[5]
        dst_seq = msg[6]
        hop_cnt = msg[7]

        self._to_log("Receive RREQ from {}".format(sender_addr))

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

        path_discovery_timer = threading.Timer(
            AODV_PATH_DISCOVERY_TIME, self.aodv_process_path_discovery_timeout, [src_addr, rreq_id]
        )
        per_node_list[rreq_id] = {
            'RREQ_ID': rreq_id,
            'Timer-Callback': path_discovery_timer
        }
        self.rreq_id_list[src_addr] = {
            'RREQ_ID_List': per_node_list
        }
        path_discovery_timer.start()

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
            route = self.routing_table[src_addr]
            if (int(route['Seq-No']) < src_seq):
                route['Seq-No'] = src_seq
                self.aodv_restart_route_timer(route, False)
            elif (int(route['Seq-No']) == src_seq):
                if (int(route['Hop-Count']) > hop_cnt):
                    route['Hop-Count'] = hop_cnt
                    route['Next-Hop'] = sender_addr
                    self.aodv_restart_route_timer(route, False)
            elif (int(route['Seq-No']) == 0):
                route['Seq-No'] = src_seq
                self.aodv_restart_route_timer(route, False)
        else:
            self.routing_table[src_addr] = {
                'Destination': str(src_addr),
                'Next-Hop': str(sender_addr),
                'Seq-No': str(src_seq),
                'Hop-Count': str(hop_cnt),
                'Status': 'Active'
            }
            self.aodv_restart_route_timer(self.routing_table[src_addr], True)

        if (self.address == dst_addr):
            self.aodv_send_rrep()
            # self.aodv_send_rrep(orig, sender, dest, dest, 0, 0)

        if (dst_addr in self.routing_table.keys()):
            pass
        else:
            pass
            # rebroadcast rreq
    def aodv_process_path_discovery_timeout(self, node, rreq_id):

        # Remove the buffered RREQ_ID for the given node
        if node in self.rreq_id_list.keys():
            node_list = self.rreq_id_list[node]
            per_node_rreq_id_list = node_list['RREQ_ID_List']
            if rreq_id in per_node_rreq_id_list.keys():
                per_node_rreq_id_list.pop(rreq_id)
    def aodv_restart_route_timer(self, route, create):
        if (create == False):
            timer = route['Lifetime']
            timer.cancel()

        timer = threading.Timer(
            AODV_ACTIVE_ROUTE_TIMEOUT, self.aodv_process_route_timeout, [route]
        )
        route['Lifetime'] = timer
        route['Status'] = 'Active'
        timer.start()
    def aodv_send_rrep(self, rrep_dest, rrep_nh, rrep_src, rrep_int_node, dest_seq_no, hop_count):
        #     def aodv_send_rrep(self, rrep_dest, rrep_nh, rrep_src, rrep_int_node, dest_seq_no, hop_count):
        #         # orig, sender, dest, dest, 0, 0
        #         # orig, sender, self.node_id, dest, route_dest_seq_no, int(route['Hop-Count']
        if (rrep_src == rrep_int_node):
            # Increment the sequence number and reset the hop count
            self.seq_no = self.seq_no + 1
            dest_seq_no = self.seq_no
            hop_count = 0
        MSG_TYPE = bytes([2])
        SENDER_ADDR = self.address
        DST_ADDR = bytes([rrep_int_node])
        DST_SEQ = bytes([dest_seq_no])
        SRC_DST = rrep_dest
        HOP_CNT = hop_count
        message = MSG_TYPE + SENDER_ADDR + DST_ADDR + DST_SEQ + SRC_DST + HOP_CNT

        self.send_implementation(message)
    def aodv_process_route_timeout(self, route):
        # Remove the route from the routing table
        key = route['Destination']
        self.routing_table.pop(key)

        self._to_log("aodv_process_route_timeout: removing " + key + " from the routing table.")
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

            rreq_content = self.RREQ_CONTENT(address, 0)

            self.send_implementation(rreq_content)

    def RREQ_CONTENT(self, DST_ADDR: bytes, seq_no: int):
        MSG_TYPE = bytes([1])
        SRC_ADDR = self.address
        SRC_SEQ = bytes([self.seq_no])
        DST_SEQ = bytes([seq_no])
        HOP_CNT = bytes([0])
        RREQ_ID = bytes([self.rreq_id])
        return MSG_TYPE + SRC_ADDR + RREQ_ID + SRC_ADDR + SRC_SEQ + DST_ADDR + DST_SEQ + HOP_CNT


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