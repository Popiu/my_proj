import select
import threading
import re
import time
import os


class ChannelSim(threading.Thread):
    def __init__(
            self, full_config: dict,
            node_list: list,
            log_dir=None
    ):
        threading.Thread.__init__(self)
        self.node_list = node_list
        self.full_config = full_config
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = self.log_dir + "/log.txt"
        self.hello_rerr_file = self.log_dir + "/hello_rerr.txt"

    def _to_log(self, log_content: str, use_log_file: str = None):
        if use_log_file is None:
            use_log_file = self.log_file
        time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
        with open(use_log_file, 'a') as f:
            f.write("[{}]:\t".format(time_stamp))
            f.write(log_content)

    def send_message(
            self, src_addr: int, message: bytes
    ):
        dst_addr = message[0]
        message = message[1:]
        msg_type = message[0]
        self._to_log(
            "{} from address {}, sending to {}\n".format(message, src_addr, dst_addr),
            use_log_file=self.hello_rerr_file if msg_type == 4 else self.log_file
        )

        if dst_addr == 255:
            for dst_node_id in range(len(self.node_list)):
                if dst_node_id != src_addr:
                    self.compute_distance_and_send_message(src_addr, dst_node_id, message)
        else:
            self.compute_distance_and_send_message(src_addr, dst_addr, message)

        self._to_log("\n", use_log_file=self.hello_rerr_file if msg_type == 4 else self.log_file)

    def compute_distance_and_send_message(self, src_addr, dst_addr, message):
        msg_type = message[0]
        if msg_type == 4:
            use_log_file = self.hello_rerr_file
        else:
            use_log_file = self.log_file
        src_pos = self.full_config["node_coords"][src_addr]
        dst_pos = self.full_config["node_coords"][dst_addr]
        distance = (dst_pos[0] - src_pos[0]) ** 2 + (dst_pos[1] - src_pos[1]) ** 2
        distance = distance ** 0.5
        if distance <= self.full_config["max_reach_dist"]:
            self._to_log(
                "{}, distance: {}, sent.\n".format(
                    dst_addr, distance
                ), use_log_file=use_log_file
            )
            # new thread
            send_thread = threading.Thread(
                target=self.send_message_to,
                args=(dst_addr, message, distance)
            )
            send_thread.start()
        else:
            self._to_log(
                "{}, distance: {}. (out of range)\n".format(
                    dst_addr, distance
                ), use_log_file=use_log_file
            )

    def send_message_to(self, dst_node_id, message, delay):
        dst_node = self.node_list[dst_node_id]
        time.sleep(delay)
        dst_node.channel_sock.sendto(message, 0, ('localhost', dst_node.comm_port))

    def run(self):
        # inputs are the channel_ports of the nodes
        inputs = []
        for node in self.node_list:
            inputs.append(node.channel_sock)
        output = []

        while True:
            readable, _, _ = select.select(inputs, [], inputs)
            for r in readable:
                src_addr = inputs.index(r)
                command, _ = r.recvfrom(100)
                self.send_message(src_addr, command)
