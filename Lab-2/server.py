import xmlrpc.server
import xmlrpc.client
import threading
import logging

# Configure logging for the server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MyServer:
    def __init__(self, port, other_ports):
        self.port = port
        self.other_ports = other_ports

    def square(self, x):
        return x * x

    def cube(self, x):
        return x * x * x

    def send_hello(self):
        # Send a "hello" message to all other nodes
        for other_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{other_port}") as proxy:
                    logging.info(f"Node on port {self.port} sending 'hello' to node on port {other_port}")
                    response = proxy.receive_hello(self.port)
                    logging.info(f"Received response: '{response}' from node on port {other_port}")
            except Exception as e:
                logging.error(f"Error sending hello to node on port {other_port}: {e}")

    def receive_hello(self, sender_port):
        # Handle receiving a "hello" message and respond with "okay"
        logging.info(f"Node on port {self.port} received 'hello' from node on port {sender_port}")
        return f"okay from node {self.port}"

def run_server(port, other_ports):
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", port), allow_none=True)
    my_server = MyServer(port, other_ports)
    server.register_instance(my_server)
    logging.info(f"Server running on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    # Define ports for the three nodes
    ports = [8000, 8001, 8002]
    threads = []

    # Start a server on each port with references to the other nodes' ports
    for i, port in enumerate(ports):
        other_ports = [p for p in ports if p != port]
        thread = threading.Thread(target=run_server, args=(port, other_ports))
        thread.start()
        threads.append(thread)

    # Join threads to keep the main program running
    for thread in threads:
        thread.join()
