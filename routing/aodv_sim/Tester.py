# Use this tester to simulate the real-world LoRaWAN network.

import os
import time
from aodv_client import Client
from channel_sim import ChannelSim


class Tester:
    def __init__(self, test_config, log_dir):
        self.test_config = test_config
        self.num_nodes = test_config["num_nodes"]
        self.input_hint = (
            "Enter a command:\n"
            "1. H or h: Help\n"
            "2. send <node_id_A> <node_id_B> <message> : Send message from A to B.\n")
        self.log_dir = os.path.join(log_dir, "logs")
        self.time_stamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

    def init_client(self):
        num_nodes = self.test_config["num_nodes"]
        node_list = []
        for i in range(num_nodes):
            node_config = {
                "comm_port": self.test_config["comm_ports"][i],
                "control_port": self.test_config["control_ports"][i],
                "channel_port": self.test_config["channel_ports"][i],
                "log_dir": os.path.join(self.log_dir, self.time_stamp, "node_" + str(i))
            }
            node_address = bytes([self.test_config["node_addresses"][i]])
            client = Client(node_address, node_config)
            node_list.append(client)
            client.start()
            # client.join()
        return node_list

    def init_channels(self):
        log_dir = os.path.join(self.log_dir, self.time_stamp, "channel_info")
        self.channels = ChannelSim(self.test_config, self.node_list, log_dir=log_dir)
        self.channels.start()


    def send_control_message(
            self, node: int, msg_type: str, contents: str
    ):
        if msg_type=="send":
            send_contents = "send" + ":" + contents
            self.node_list[node].control_sock.sendto(
                send_contents.encode("utf-8"),
                0, ('localhost', self.node_list[node].control_port)
            )

    def main(self):
        # Initialize the client
        self.node_list = self.init_client()

        # Initialize the channels
        self.init_channels()

        # Set the prompt
        prompt = "TESTER" + "> "

        # Listen indefinitely for user inputs
        print(self.input_hint)
        while (True):
            command = input(prompt)
            command = command.split(" ")
            if command[0] == "H" or command[0] == "h":
                print(self.input_hint)
            elif command[0] == "send":
                node_id_A = int(command[1])
                node_id_B = int(command[2])
                message = command[3]
                contents = str(node_id_B) + ":" + message
                self.send_control_message(
                    node_id_A, msg_type="send",
                    contents=contents
                )
            else:
                print("Invalid command.")
