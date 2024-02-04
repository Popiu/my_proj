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

    def _to_log(self, log_content: str):
        time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
        with open(self.log_file, 'a') as f:
            f.write("[{}]:\t".format(time_stamp))
            f.write(log_content)

    def send_message(self, src_node_id, message):
        src_pos = self.full_config["node_coords"][src_node_id]
        for dst_node_id in range(len(self.node_list)):
            if dst_node_id != src_node_id:
                dst_pos = self.full_config["node_coords"][dst_node_id]
                distance = (dst_pos[0] - src_pos[0]) ** 2 + (dst_pos[1] - src_pos[1]) ** 2
                if distance <= self.full_config["max_reach_dist"]:
                    self._to_log(
                        "Sending message from {} to {}, distance: {}".format(
                        src_node_id, dst_node_id, distance
                        )
                    )
                    # new thread
                    send_thread = threading.Thread(
                        target=self.send_message_to,
                        args=(dst_node_id, message, distance)
                    )
                    send_thread.start()

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
                src_node_id = inputs.index(r)
                # broadcast this message to other nodes
                command, _ = r.recvfrom(100)
                self._to_log(str(command)+"\n")
                self.send_message(src_node_id, command)
