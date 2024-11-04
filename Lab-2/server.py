import xmlrpc.server
import xmlrpc.client
import threading
import logging
import os
import sys

# Configure logging for the server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MyServer:
    def __init__(self, port, other_ports):
        self.port = port
        self.other_ports = other_ports
        self.file_path = f"{port}/CISC5597.txt"

        # Create a directory for the node and the file if they don't exist
        os.makedirs(str(port), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("")  # Initialize the file as empty

    def square(self, x):
        result = x * x
        self.broadcast_result(f"Square of {x} is {result}")
        return result

    def cube(self, x):
        result = x * x * x
        self.broadcast_result(f"Cube of {x} is {result}")
        return result

    def broadcast_result(self, message):
        """Send the result to all other nodes."""
        logging.info(f"Node on port {self.port} broadcasting result: '{message}'")
        for other_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{other_port}") as proxy:
                    proxy.receive_result(message)
                    logging.info(f"Node on port {self.port} sent result to node on port {other_port}")
            except Exception as e:
                logging.error(f"Error sending result to node on port {other_port}: {e}")

    def receive_result(self, message):
        """Receive a result from another node and write it to CISC5597.txt."""
        logging.info(f"Node on port {self.port} received result: '{message}'")
        with open(self.file_path, 'a') as f:
            f.write(message + "\n")
        return "Result received and saved"

def run_server(port, other_ports):
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", port), allow_none=True)
    my_server = MyServer(port, other_ports)
    server.register_instance(my_server)
    logging.info(f"Server running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port_number>")
        sys.exit(1)

    # Get the specified port from the command-line argument
    port = int(sys.argv[1])
    
    # Define all ports in the network
    all_ports = [8000, 8001, 8002]
    
    if port not in all_ports:
        print(f"Error: Invalid port {port}. Allowed ports are {all_ports}.")
        sys.exit(1)

    # Determine the other ports for broadcasting
    other_ports = [p for p in all_ports if p != port]

    # Run the server on the specified port
    run_server(port, other_ports)
