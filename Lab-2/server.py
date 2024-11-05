import xmlrpc.server
import xmlrpc.client
import threading
import logging
import os
import sys
from datetime import datetime
from termcolor import colored  # For colored logging

# Configure logging for the server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Proposal:
    def __init__(self, proposal_id, value):
        self.proposal_id = proposal_id
        self.value = value


class Acceptor:
    def __init__(self):
        self.minProposal = None
        self.acceptedProposal = None
        self.acceptedValue = None

    def prepare(self, proposal_id):
        if self.minProposal is None or proposal_id > self.minProposal:
            self.minProposal = proposal_id
            return self.acceptedProposal, self.acceptedValue
        return None, None

    def accept(self, proposal):
        if proposal.proposal_id >= self.minProposal:
            self.minProposal = proposal.proposal_id
            self.acceptedProposal = proposal.proposal_id
            self.acceptedValue = proposal.value
            return True
        return False


class MyServer:
    def __init__(self, port, other_ports):
        self.port = port
        self.other_ports = other_ports
        self.file_path = f"{port}/CISC5597.txt"
        self.proposer_id = port  # Use port as unique proposer ID
        self.acceptors = [Acceptor() for _ in other_ports]  # Acceptor instances for other nodes
        os.makedirs(str(port), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("")  # Initialize the file as empty

    def propose_value(self, value):
        """Propose a value using the Paxos algorithm."""
        logging.info(colored(f"Node on port {self.port} proposing value: {value}", 'blue'))
        
        proposal_id = self.proposer_id
        proposals = {}
        promises = 0

        # Prepare phase
        for acceptor_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") as proxy:
                    accepted_id, accepted_value = proxy.prepare(proposal_id)
                    if accepted_id is not None:
                        proposals[accepted_id] = accepted_value
                    promises += 1
            except Exception as e:
                logging.error(f"Error during prepare phase with node {acceptor_port}: {e}")

        if promises > len(self.other_ports) // 2:
            if proposals:
                # If any previous values were accepted, use the highest one
                accepted_value = max(proposals.items(), key=lambda x: x[0])[1]
                value = accepted_value
                logging.info(colored(f"Node on port {self.port} using previous value: {value}", 'green'))

            # Accept phase
            accepted_count = 0
            for acceptor_port in self.other_ports:
                proposal = Proposal(proposal_id, value)
                try:
                    with xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") as proxy:
                       if proxy.accept(proposal.__dict__):
                            accepted_count += 1
                except Exception as e:
                    logging.error(f"Error during accept phase with node {acceptor_port}: {e}")

            if accepted_count > len(self.other_ports) // 2:
                # Commit phase
                self.update_file(value)
                self.broadcast_commit(value)
                return f"Value '{value}' has been updated and committed."

        return "Failed to reach consensus."

    def prepare(self, proposal_id):
        """Handle prepare requests from proposers."""
        logging.info(colored(f"Node on port {self.port} received prepare request with ID: {proposal_id}", 'yellow'))
        return self.acceptors[0].prepare(proposal_id)

    # the accept method to handle both dict and Proposal objects
    def accept(self, proposal):
        """Handle accept requests from proposers."""
        if isinstance(proposal, dict):
            # If a dict is received, convert it to a Proposal object
            proposal = Proposal(proposal['proposal_id'], proposal['value'])
        elif not isinstance(proposal, Proposal):
            logging.error(f"Invalid proposal type: {type(proposal)}. Expected Proposal or dict.")
            return False

        logging.info(colored(f"Node on port {self.port} received accept request with ID: {proposal.proposal_id} and value: {proposal.value}", 'yellow'))
        return self.acceptors[0].accept(proposal)

    def update_file(self, value):
        """Update the local CISC5597.txt file with the new value."""
        with open(self.file_path, 'a') as f:  # Append new value to the file
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Set value to: {value}\n")
        logging.info(colored(f"Node on port {self.port} updated file with value: '{value}'", 'green'))

    def broadcast_commit(self, value):
        """Broadcast the commit message to all other nodes."""
        logging.info(colored(f"Node on port {self.port} broadcasting commit value: '{value}'", 'blue'))
        for other_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{other_port}") as proxy:
                    proxy.receive_commit(value)
            except Exception as e:
                logging.error(f"Error sending commit to node on port {other_port}: {e}")

    def receive_commit(self, value):
        """Receive a commit message from another node."""
        logging.info(colored(f"Node on port {self.port} received commit for value: '{value}'", 'yellow'))
        self.update_file(value)

def run_server(port, other_ports):
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", port), allow_none=True)
    my_server = MyServer(port, other_ports)
    server.register_instance(my_server)
    logging.info(colored(f"Server running on port {port}...", 'cyan'))
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
