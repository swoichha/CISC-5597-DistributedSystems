import xmlrpc.server
import xmlrpc.client
import threading
import random
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
        # Initializing with None for the 1st Proposal as they haven't been set yet.
        self.minProposal = None
        self.acceptedProposal = None
        self.acceptedValue = None
        self.promise = False

    # Step 3: Respond to Prepare(n) from Proposer:
    def prepare(self, proposal_id):
        logging.info(colored(f"RECEIVED: Prepare {proposal_id} for new proposal", 'green'))
        """If self.minProposal is None (first proposal) or proposal_id > self.minProposal,
        update minProposal and promise to accept the proposal"""
        
        if self.minProposal is None or proposal_id > self.minProposal:
            self.minProposal = proposal_id
            self.promise = True
            logging.info(colored(f"STEP 3: Respond to Prepare({proposal_id}): Setting minProposal to {proposal_id}", 'green'))

        # If proposal_id is smaller than the current minProposal, reject the proposal
        else:
            self.promise = False
            logging.info(colored(f"STEP 3: Respond to Prepare({proposal_id}): Rejected proposal because {proposal_id} < {self.minProposal}", 'red'))

        return self.acceptedProposal, self.acceptedValue, self.promise

    def accept(self, proposal):
        if proposal.proposal_id >= self.minProposal:
            self.minProposal = proposal.proposal_id
            self.acceptedProposal = proposal.proposal_id
            self.acceptedValue = proposal.value
            logging.info(colored(f"STEP 6: Respond to Accept({proposal.proposal_id},{proposal.value})", 'yellow'))
            return True
        return False

# Paxos Algorithm Implementation
highestNum = 0
highestNum_lock = threading.Lock()  # To synchronize access to `highestNum`

class MyServer:
    def __init__(self, port, other_ports):
        self.port = port
        self.other_ports = other_ports
        self.file_path = f"{port}/CISC5597.txt"
        self.proposer_id = random.randint(1, 999)   # use random value for proposal ID
        self.acceptors = [Acceptor() for _ in other_ports]  # Acceptor instances for other nodes
        os.makedirs(str(port), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("")  # Initialize the file as empty        

    def propose_value(self, value, A_win = True, delay_value =0):
        # to track the highest proposal number encountered
        global highestNum
        # Lock access to `highestNum` to avoid race conditions
        with highestNum_lock:
            # Get the current highestNum across all nodes
            self.sync_highestNum()
            print("//////////", highestNum)
            
            # Determine proposal_id based on global highestNum
            if highestNum >= self.proposer_id:
                # Ensure the new proposal_id is always higher
                proposal_id = highestNum + 1
            else:
                # If proposer_id is higher, use it and update highestNum
                proposal_id = self.proposer_id
            print("********", proposal_id)

            # Update global `highestNum` to be the latest used proposal ID
            highestNum = proposal_id
        print(self.proposer_id,proposal_id,"*-*-*-*----*-*-- proposal id", highestNum)

        proposals = {}
        promises = 0
        required_majority = 2 #we do not count the node that sends the req to itself 

        # Prepare Phase
        promises, proposals = self.prepare_phase(proposal_id)

        # Step 4: Check if majority response were received, if so then proceed to Accept Phase
        if promises >= required_majority:
            if proposals:

                highest_proposal_id = max(proposals)

                # accepted_value = proposals[highest_proposal_id]
                value = proposals[highest_proposal_id]  # Replace proposed value with the accepted value for highest accepted proposal ID
                logging.info(colored(f"STEP 4.2: Using previously accepted value: {value} from proposal ID: {highest_proposal_id}", 'cyan'))

            # Accept phase
            if self.accept_phase(proposal_id, value, required_majority):
                logging.info(colored(f"Consensus reached on value: {value}. Broadcasting commit.", 'blue'))
                self.broadcast_commit(value)
                return f"Value '{value}' has been updated and committed."

        return "Failed to reach consensus."
    
    def sync_highestNum(self):
        """ Synchronize the highestNum value across all nodes by querying other nodes. """
        global highestNum
        # Sync highestNum by asking other nodes
        for acceptor_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") as proxy:
                    # Get the latest highestNum from the acceptor node
                    highestNum_from_node = proxy.get_highestNum()
                    # Update the global highestNum if the node's value is higher
                    if highestNum_from_node > highestNum:
                        highestNum = highestNum_from_node
            except Exception as e:
                print(f"Error syncing highestNum with node {acceptor_port}: {e}")

    def get_highestNum(self):
        """ Get the current highest proposal number. """
        global highestNum
        return highestNum
    
    def prepare_phase(self, proposal_id):
        promises, proposals = 0, {}
        logging.info(colored(f"STEP 1: PREPARE({proposal_id}) by node {self.port}", 'blue'))

        for acceptor_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") as proxy:
                    
                    # Step 2: Broadcast Prepare(n) to all servers
                    logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_id}) to all servers by node {self.port}", 'blue'))
                    acceptedProposal_id, accepted_value, received_promise = proxy.prepare(proposal_id)
                    # Step 4: Receiving response for step-2
                    logging.info(colored(f"STEP 4: Received Respond to Prepare({proposal_id}) from {acceptor_port}", 'blue'))
                    if received_promise:
                        promises += 1

                    """This will be executed only if step 2 returned a previously set value on acceptedValue"""
                    if accepted_value:
                        logging.info(colored(f"STEP 4.1: acceptedValue: {accepted_value} was returned in the response from node {acceptor_port} with proposal ID: {acceptedProposal_id}", 'cyan'))
                        proposals[acceptedProposal_id] = accepted_value

            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {acceptor_port}: {e}", "red"))
        
        return promises, proposals

    def accept_phase(self, proposal_id, value, required_majority):
        accepted_count = 0
        proposal = Proposal(proposal_id, value)
        
        for acceptor_port in self.other_ports:
            try:
                with xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") as proxy:
                    logging.info(colored(f"STEP 5: Broadcast Accept({proposal_id},{value}) to server {acceptor_port}", 'blue'))
                    if proxy.accept(proposal.__dict__):
                        accepted_count += 1
            except Exception as e:
                logging.error(f"Error during accept phase with node {acceptor_port}: {e}")
        
        return accepted_count >= required_majority

# Broadcast Prepare(n) to all servers
    def prepare(self, proposal_id):
        """Handle prepare requests from proposers."""
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

        return self.acceptors[0].accept(proposal)

    def update_file(self, value):
        """Update the local CISC5597.txt file with the new value."""
        with open(self.file_path, 'w') as f:  # Append new value to the file
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Set value to: {value}\n")
        logging.info(colored(f"Node on port {self.port} updated file with value: '{value}'", 'green'))

    def broadcast_commit(self, value):
        """Broadcast the commit message to all other nodes."""
        logging.info(colored(f"Node on port {self.port} broadcasting commit value: '{value}'", 'yellow'))
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

    def restart(self):
        """Reset the server state to its initial conditions."""
        logging.info(colored(f"Restarting server on port {self.port} to initial state...", 'yellow'))
        
        # Reset proposal-related variables
        global highestNum
        highestNum = 0  # Reset global highestNum
        
        # Reset acceptor state for this server
        for acceptor in self.acceptors:
            acceptor.minProposal = None
            acceptor.acceptedProposal = None
            acceptor.acceptedValue = None
            acceptor.promise = False
        
        logging.info(colored(f"Server on port {self.port} has been reset.", 'green'))

    # Method to expose restart functionality to XML-RPC
    def restart_server(self):
        """Handle XML-RPC request to restart the server."""
        self.restart()
        return "Server has been restarted."
    
def run_server(port, other_ports):
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", port), allow_none=True)
    my_server = MyServer(port, other_ports)
    server.register_instance(my_server)
    logging.info(colored(f"Server running on port {port}...", 'green'))
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
        print(f"\033[91m\nError: Invalid port {port}. Allowed ports are {all_ports}.\033[0m")
        sys.exit(1)

    # Determine the other ports for broadcasting
    other_ports = [p for p in all_ports if p != port]

    # Run the server on the specified port
    run_server(port, other_ports)
