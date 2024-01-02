class tester:
    def __init__(self):
        self.num_nodes = 0
        self.sock = 0
        self.port = 0
        self.command = ""

    def main(self, n):
        # Store the node count
        self.num_nodes = n

        # # Setup the port to be used for communication with data nodes
        # self.port = TESTER_PORT
        #
        # # Setup socket to communicate with the AODV protocol handler thread
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.bind(('localhost', self.port))
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Set the prompt
        prompt = "TESTER" + "> "

        # Listen indefinitely for user inputs
        while (True):
            command = input(prompt)

            # {'help': self.help,
            #  'run_test_script': self.run_test_script}.get(command, self.default)()