class Tester:
    def __init__(self, test_config):
        self.test_config = test_config
        self.num_nodes = test_config["num_nodes"]
        self.input_hint = (
            "Enter a command:\n"
            "1. H or h: Help\n"
            "2. send <node_id_A> <node_id_B> <message> : Send message from A to B.\n")

    def main(self):

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
                # self.send_message(node_id_A, node_id_B, message)
            else:
                print("Invalid command.")