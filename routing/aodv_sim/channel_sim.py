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
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = self.log_dir + "/log.txt"

    def _to_log(self, log_content: str):
        time_stamp = time.strftime("%Y-%m-%d: %H:%M:%S", time.localtime())
        with open(self.log_file, 'a') as f:
            f.write("[{}]:\t".format(time_stamp))
            f.write(log_content)

    def run(self):
        # inputs are the channel_ports of the nodes
        inputs = []
        for node in self.node_list:
            inputs.append(node.channel_sock)
        output = []

        while True:
            readable, _, _ = select.select(inputs, [], inputs)
            for r in readable:
                print(inputs.index(r))
