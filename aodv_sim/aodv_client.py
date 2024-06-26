from routing_table import RoutingTab, routing_entry
import threading
import socket, select
import os
import re
import time
import platform

# protocol type
# 0: regular
# 1: RREQ
# msg_type(1 byte) send_addr(1 byte) receiver(1 byte) rreq_id(1 byte) rreq_src_addr(1 byte) src_seq(1 byte) dst_addr(1 byte) dst_seq(1 byte) hop_cnt(1 byte)
# 2: RREP
# msg_type(1 byte) send_addr(1 byte) receiver(1 byte)
# 3: RERR
#
# 4: HELLO

AODV_HELLO_INTERVAL = 10
AODV_HELLO_TIMEOUT = 30
AODV_PATH_DISCOVERY_TIME = 30
AODV_ACTIVE_ROUTE_TIMEOUT = 300


class Client(threading.Thread):
    def __init__(
            self, address: bytes, client_config: dict
    ):
        threading.Thread.__init__(self)
        assert len(address) == 1  # one byte
        self.address = address
        self.address_str = str(int.from_bytes(address, byteorder='big'))
        self.routing_table = dict()
        self.seq_no = 0  # maintaining sequence number
        self.rreq_id = 0  # maintaining the rreq id
        self.rreq_id_list = {}
        self.pending_msg_q = []
        self.neighbors = dict()

        # Only for simulation
        self.log_on = True
        self.client_config = client_config
        self.comm_port = client_config["comm_port"]
        self.control_port = client_config["control_port"]
        self.channel_port = client_config["channel_port"]
        self.log_dir = client_config["log_dir"]
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = self.log_dir + "/log.txt"
        self.hello_rerr_file = self.log_dir + "/hello_rerr.txt"

        self._bind_ports()

    def aodv_process_path_discovery_timeout(
            self, address: str, rreq_id: int
    ):
        if address in self.rreq_id_list.keys():
            per_node_list = self.rreq_id_list[address]
            if rreq_id in per_node_list.keys():
                per_node_list.pop(rreq_id)

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

        self._to_log("Send RREP to {}\n\n".format(rrep_nh))

        if rrep_src == rrep_int_node:
            self.seq_no = self.seq_no + 1
            dest_seq_no = self.seq_no
            hop_count = 0

        msg_type = bytes([2])
        sender_addr = self.address
        recv_addr = bytes([int(rrep_nh)])
        dst_addr = bytes([int(rrep_int_node)])
        dst_seq = bytes([dest_seq_no])
        src_dst = bytes([int(rrep_dest)])
        hop_cnt = bytes([hop_count])
        message = msg_type + sender_addr + recv_addr + dst_addr + dst_seq + src_dst + hop_cnt

        self.send_implementation(recv_addr, message)

    def aodv_process_rrep_msg(self, msg):
        msg_type = msg[0]
        sender_addr = msg[1]
        recv_addr = msg[2]
        dst_addr = msg[3]
        dst_seq = msg[4]
        src_addr = msg[5]
        hop_cnt = msg[6] + 1
        msg_bytearray = bytearray(msg)
        msg_bytearray[6] = hop_cnt
        msg = bytes(msg_bytearray)

        src_addr = str(src_addr)
        dst_addr = str(dst_addr)

        self._to_log("Receive RREP from {}\n\n".format(sender_addr))

        if self.address_str == src_addr:
            if dst_addr in self.routing_table.keys():
                route = self.routing_table[dst_addr]
                route_hop_count = int(route['Hop-Count'])
                if route_hop_count > hop_cnt:
                    route['Hop-Count'] = str(hop_cnt)
                    self.aodv_restart_route_timer(self.routing_table[dst_addr], False)
                elif route['Status'] == 'Inactive':
                    self.routing_table[dst_addr] = {
                        'Destination': dst_addr,
                        'Next-Hop': str(sender_addr),
                        'Seq-No': str(dst_seq),
                        'Hop-Count': str(hop_cnt),
                        'Status': 'Active'
                    }
                    self.aodv_restart_route_timer(self.routing_table[dst_addr], True)
            else:
                self.routing_table[dst_addr] = {
                    'Destination': dst_addr,
                    'Next-Hop': str(sender_addr),
                    'Seq-No': str(dst_seq),
                    'Hop-Count': str(hop_cnt),
                    'Status': 'Active'
                }
                self.aodv_restart_route_timer(self.routing_table[dst_addr], True)
            # check if we have any pending messages to this destination
            for message in self.pending_msg_q:
                msg_dst = message[2]
                if msg_dst == int(dst_addr):
                    # send this msg to the dst_addr
                    next_hop = sender_addr
                    self.send_implementation(bytes([next_hop]), message)
                    self.pending_msg_q.remove(message)
        else:
            # forward this rrep
            if dst_addr in self.routing_table.keys():
                route = self.routing_table[dst_addr]
                route['Status'] = 'Active'
                route["Seq-No"] = str(dst_seq)
                next_hop = route['Next-Hop']
                self.send_implementation(next_hop, msg)
            else:
                self.routing_table[dst_addr] = {
                    'Destination': dst_addr,
                    'Next-Hop': str(sender_addr),
                    'Seq-No': str(dst_seq),
                    'Hop-Count': str(hop_cnt),
                    'Status': 'Active'
                }
                self.aodv_restart_route_timer(self.routing_table[dst_addr], True)
            route = self.routing_table[src_addr]
            next_hop = route['Next-Hop']
            self.aodv_forward_rrep(next_hop, msg)

    def aodv_forward_rrep(self, next_hop, msg):
        msg_bytearray = bytearray(msg)
        msg_bytearray[1] = int(self.address_str)
        msg_bytearray[2] = int(next_hop)
        msg = bytes(msg_bytearray)
        self.send_implementation(bytes([int(next_hop)]), msg)

    def aodv_process_route_timeout(self, route):
        # Remove the route from the routing table
        key = route['Destination']
        self.routing_table.pop(key)

        self._to_log("aodv_process_route_timeout: removing " + key + " from the routing table.")

    def aodv_send_message(
            self, address: str, message: str
    ):
        addr_byte = bytes([int(address)])
        message_content = bytes([0]) + self.address + addr_byte + message.encode('utf-8')

        if address in self.routing_table.keys():
            if self.routing_table[address]['Status'] == 'Inactive':
                self.aodv_send_rreq(address, int(self.routing_table[address]['Seq-No']))
                self._to_log("Route not active, send RREQ for dst_addr {}.\n\n".format(address))
                self.pending_msg_q.append(message_content)
            else:
                next_hop = self.routing_table[address]['Next-Hop']
                self.send_implementation(bytes([int(next_hop)]), message_content)
                self._to_log("Route active, send to {} via {}.\n\n".format(address, next_hop))
                self.aodv_restart_route_timer(self.routing_table[address], False)
        else:
            self.aodv_send_rreq(address, 0)

            self.pending_msg_q.append(message_content)

    def aodv_send_rreq(
            self, dst_addr: str, seq_no: int
    ):
        self.seq_no = self.seq_no + 1
        self.rreq_id = self.rreq_id + 1

        self._to_log("Broadcast RREQ to find the route to {}.\n\n".format(dst_addr))

        msg_type = bytes([1])
        sender_addr = self.address
        recv_addr = bytes([255])
        rreq_id = bytes([self.rreq_id])
        src_addr = self.address
        src_seq = bytes([self.seq_no])
        dst_addr = bytes([int(dst_addr)])
        dst_seq = bytes([seq_no])
        hop_cnt = bytes([0])

        rreq_content = msg_type + sender_addr + recv_addr + rreq_id + src_addr + src_seq + dst_addr + dst_seq + hop_cnt
        self.send_implementation(recv_addr, rreq_content)

        rreq_id_int = int.from_bytes(rreq_id, byteorder='big')
        # Buffer the RREQ_ID for PATH_DISCOVERY_TIME. This is used to discard duplicate RREQ messages
        path_discovery_timer = threading.Timer(
            AODV_PATH_DISCOVERY_TIME, self.aodv_process_path_discovery_timeout, [self.address, rreq_id_int]
        )
        per_node_list = self.rreq_id_list.get(self.address_str, dict())
        per_node_list[rreq_id_int] = {
            'RREQ_ID': rreq_id_int, 'Timer-Callback': path_discovery_timer
        }
        self.rreq_id_list[self.address_str] = per_node_list
        path_discovery_timer.start()

    def aodv_process_rreq_msg(self, msg: bytes):
        msg_type = msg[0]
        sender_addr = msg[1]
        recv_addr = msg[2]
        rreq_id = msg[3]
        src_addr = msg[4]
        src_seq = msg[5]
        dst_addr = msg[6]
        dst_seq = msg[7]
        hop_cnt = msg[8] + 1
        msg_bytearray = bytearray(msg)
        msg_bytearray[8] = hop_cnt
        msg = bytes(msg_bytearray)

        src_addr = str(src_addr)
        dst_addr = str(dst_addr)
        sender_addr = str(sender_addr)

        # Discard this RREQ if we have already received this before
        if (src_addr in self.rreq_id_list.keys()):
            per_node_list = self.rreq_id_list[src_addr]
            if rreq_id in per_node_list.keys():
                self._to_log("Receive RREQ of {} from {}\n".format(src_addr, sender_addr))
                self._to_log("Discard this RREQ\n\n")
                return

        self._to_log("Receive RREQ of {} from {}\n\n".format(src_addr, sender_addr))

        # This is a new RREQ message. Buffer it first
        per_node_list = self.rreq_id_list.get(src_addr, dict())

        path_discovery_timer = threading.Timer(
            AODV_PATH_DISCOVERY_TIME, self.aodv_process_path_discovery_timeout, [src_addr, rreq_id]
        )
        per_node_list[rreq_id] = {
            'RREQ_ID': rreq_id,
            'Timer-Callback': path_discovery_timer
        }
        self.rreq_id_list[src_addr] = per_node_list
        path_discovery_timer.start()

        if src_addr in self.routing_table.keys():
            route = self.routing_table[src_addr]
            if int(route['Seq-No']) < src_seq:
                route['Seq-No'] = str(src_seq)
                self.aodv_restart_route_timer(route, False)
            elif int(route['Seq-No']) == src_seq:
                if int(route['Hop-Count']) > hop_cnt:
                    route['Hop-Count'] = str(hop_cnt)
                    route['Next-Hop'] = str(sender_addr)
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

        if self.address_str == dst_addr:
            self.aodv_send_rrep(src_addr, sender_addr, dst_addr, dst_addr, 0, 0)
            return

        if dst_addr in self.routing_table.keys():
            route = self.routing_table[dst_addr]
            status = route['Status']
            route_dest_seq_no = int(route['Seq-No'])
            if route_dest_seq_no >= dst_seq and status == "Active":
                self.aodv_send_rrep(src_addr, sender_addr, self.address_str, dst_addr, route_dest_seq_no, int(route['Hop-Count']))
                return
        else:
            # Rebroadcast the RREQ
            self.aodv_forward_rreq(msg)

    def aodv_forward_rreq(self, msg):
        self._to_log("Forward RREQ of {} to all neighbors.\n\n".format(msg[4]))
        msg_bytearray = bytearray(msg)
        msg_bytearray[1] = int(self.address_str)
        msg_bytearray[2] = 255
        msg = bytes(msg_bytearray)
        self.send_implementation(bytes([255]), msg)

    # # Only for simulation, the implementation with LoRa should be different
    def send_implementation(
            self, address: bytes, message: bytes
    ):
        full_content = address + message
        self.channel_sock.sendto(full_content, 0, ('localhost', self.channel_port))

    def _to_log(self, log_content: str, use_log_file: str = None):
        if use_log_file is None:
            use_log_file = self.log_file

        if self.log_on:
            time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
            with open(use_log_file, 'a') as f:
                f.write("[{}]:\t".format(time_stamp))
                f.write(log_content)

    def _bind_ports(self):
        # determine what OS is running
        os_sys = platform.system().lower()

        if os_sys == "linux" or os_sys == "macos":
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

    def show_routing_table(self):
        print("")
        print("There are " + str(len(self.routing_table)) + " active route(s) in the routing-table")
        print("")

        print("Destination     Next-Hop     Seq-No     Hop-Count     Status")
        print("------------------------------------------------------------")
        for r in self.routing_table.values():
            print(r['Destination'] + "              " + r['Next-Hop'] + "           " + r['Seq-No'] + "          " + r[
                'Hop-Count'] + "             " + r['Status'])
        print("")

    def aodv_send_hello_message(self):

        hello_msg = bytes([4]) + self.address + bytes([255])
        self.send_implementation(bytes([255]), hello_msg)
        self._to_log(
            "Send hello message to 255.\n\n",
            use_log_file=self.hello_rerr_file
        )

        # Restart the timer
        self.hello_timer.cancel()
        self.hello_timer = threading.Timer(AODV_HELLO_INTERVAL, self.aodv_send_hello_message, ())
        self.hello_timer.start()

    def aodv_process_hello_message(self, message):
        sender_addr = message[1]
        sender_addr = str(sender_addr)

        self._to_log("Receive hello message from {}.\n\n".format(sender_addr), use_log_file=self.hello_rerr_file)

        if sender_addr in self.neighbors.keys():
            neighbor = self.neighbors[sender_addr]
            timer = neighbor['Timer-Callback']
            timer.cancel()
            timer = threading.Timer(AODV_HELLO_TIMEOUT,
                                    self.aodv_process_neighbor_timeout, [sender_addr])
            self.neighbors[sender_addr] = {'Neighbor': sender_addr,
                                           'Timer-Callback': timer}
            timer.start()
            # Restart the lifetime timer
            route = self.routing_table[sender_addr]
            self.aodv_restart_route_timer(route, False)
        else:
            timer = threading.Timer(AODV_HELLO_TIMEOUT,
                                    self.aodv_process_neighbor_timeout, [sender_addr])
            self.neighbors[sender_addr] = {'Neighbor': sender_addr,
                                           'Timer-Callback': timer}
            timer.start()

        if (sender_addr in self.routing_table.keys()):
            route = self.routing_table[sender_addr]
            self.aodv_restart_route_timer(route, False)
        else:
            self.routing_table[sender_addr] = {
                'Destination': sender_addr,
                'Next-Hop': sender_addr,
                'Seq-No': '1',
                'Hop-Count': '1',
                'Status': 'Active'}
            self.aodv_restart_route_timer(self.routing_table[sender_addr], True)

    def aodv_process_neighbor_timeout(self, neighbor):
        # Update the routing table. Mark the route as inactive.
        route = self.routing_table[neighbor]
        route['Status'] = 'Inactive'

        # Iterate through the routing table and remove all the routes that have the neighbor as the next hop
        keys_to_remove = []
        for key in self.routing_table.keys():
            if self.routing_table[key]['Next-Hop'] == neighbor and key != neighbor:
                self.routing_table[key]['Status'] = 'Inactive'

        # log this event
        self._to_log("aodv_process_neighbor_timeout: " + neighbor + " is inactive.\n")

        # Send an RERR to all the neighbors
        self.aodv_send_rerr(neighbor, int(route['Seq-No']))

        # Try to repair the route
        dest_seq_no = int(route['Seq-No']) + 1
        self.aodv_send_rreq(neighbor, dest_seq_no)

    def aodv_send_rerr(self, dest_addr, dest_seq_no):
        msg_type = bytes([3])
        sender_addr = self.address
        recv_addr = bytes([255])
        dst_addr = bytes([int(dest_addr)])
        dst_seq = bytes([dest_seq_no])
        msg = msg_type + sender_addr + recv_addr + dst_addr + dst_seq

        for n in self.neighbors.keys():
            self._to_log("Send RERR to {}.\n\n".format(n))
            self.send_implementation(bytes([int(n)]), msg)

        if dst_addr in self.routing_table.keys():
            route = self.routing_table[dst_addr]
            if route['Status'] == 'Active' and route['Next-Hop'] == sender_addr:
                # Mark the destination as inactive
                route['Status'] = "Inactive"

                # Forward the RERR to all the neighbors
                self.aodv_forward_rerr(msg)
            # else:
            #     logging.debug("['" + message_type + "', 'Ignoring RERR for " + dest + " from " + sender + "']")

    def aodv_forward_rerr(self, msg):
        msg_bytearray = bytearray(msg)
        msg_bytearray[1] = int(self.address_str)
        msg_bytearray[2] = 255
        msg = bytes(msg_bytearray)
        for n in self.neighbors.keys():
            self.send_implementation(bytes([n]), msg)

    def aodv_process_rerr_msg(self, msg):
        sender = msg[1]
        dest = msg[3]
        dest_seq_no = int(msg[4])

        self._to_log("Receive RERR from {} for {}.\n\n".format(sender, dest))

        if (int(self.address_str) == dest):
            return

        if str(dest) in self.routing_table.keys():
            route = self.routing_table[str(dest)]
            if route['Status'] == 'Active' and route['Next-Hop'] == str(sender):
                # Mark the destination as inactive
                route['Status'] = 'Inactive'

                # Forward the RERR to all the neighbors
                self.aodv_forward_rerr(msg)

    def run(self):

        # Start the hello timer
        self.hello_timer = threading.Timer(AODV_HELLO_INTERVAL, self.aodv_send_hello_message, ())
        self.hello_timer.start()

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
                        self._to_log("Sending command, send to {}, {}\n".format(command_list[1], command_list[2]))
                        self.aodv_send_message(command_list[1], command_list[2])
                    elif command_type == "show":
                        self.show_routing_table()
                elif r is self.comm_sock:
                    command, _ = self.comm_sock.recvfrom(100)
                    command_type = command[0]
                    recv_addr = command[2]
                    if recv_addr == int(self.address_str) or recv_addr == 255:
                        if command_type == 0:
                            # regular message
                            self._to_log("Receive packet, {}\n".format(str(command)))
                        elif command_type == 1:
                            self.aodv_process_rreq_msg(command)
                        elif command_type == 2:
                            self.aodv_process_rrep_msg(command)
                        elif command_type == 3:
                            self.aodv_process_rerr_msg(command)
                        elif command_type == 4:
                            self.aodv_process_hello_message(command)
                    else:
                        if command_type == 0:
                            route = self.routing_table[str(recv_addr)]
                            next_hop = route['Next-Hop']
                            self.aodv_restart_route_timer(route, False)
                            if route['Status'] == 'Active':
                                self.send_implementation(bytes([int(next_hop)]), command)
                            else:
                                self.aodv_send_rreq(str(recv_addr), int(route['Seq-No']))
                                self.pending_msg_q.append(command)
                    #     self.routing_table.add_routing_entry(routing_entry(command[1:]))
                    # self._to_log("Receive packet, {}".format(str(command)))
