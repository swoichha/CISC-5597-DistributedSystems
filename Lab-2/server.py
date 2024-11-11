import xmlrpc.server
import xmlrpc.client
import threading
import logging
import os
import sys
from datetime import datetime
from termcolor import colored  # For colored logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# from server1 import MyServer

# Global variables
acceptedProposal = None
acceptedValue = None
acceptedProposal_lock = threading.Lock()
acceptedValue_lock = threading.Lock()

class MyServer:
    def __init__(self,port, other_ports):
        self.port = port
        self.other_ports = None
        self.minProposal = None
        # self.acceptedProposal = None
        # self.acceptedValue = None
        self.peers = None
        self.promise = False
        self.file_path = f"{port}/CISC5597.txt"
        os.makedirs(str(port), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("")

    def reset_file(self):
        """Clear the contents of the CISC5597.txt file."""
        with open(self.file_path, 'w') as f:
            f.write("")

    def restart(self):
        """Resets the state of the node to initial values."""
        global acceptedProposal, acceptedValue
        logging.info(colored(f"Restarting node on port {self.port}", 'yellow'))
        with acceptedProposal_lock:
            acceptedProposal = None
        with acceptedValue_lock:
            acceptedValue = None
        self.minProposal = None
        self.promise = False
        self.reset_file()  # Clear file contents
        logging.info(colored(f"Node on port {self.port} has been reset to initial state.", 'green'))

    def accept(self, proposal_n, value):
        global acceptedProposal,acceptedValue
        if self.minProposal is None or proposal_n >= self.minProposal:
            self.minProposal = proposal_n
            with acceptedProposal_lock:
                   acceptedProposal = proposal_n
            with acceptedValue_lock:
                acceptedValue = value
            return True  # Accept the proposal
        else:
            return False

    def broadcast_commit(self, value,peers):
        """Broadcast the commit message to all other nodes."""
        logging.info(colored(f"Node on port {self.port} broadcasting commit value: '{value}'", 'blue'))
        for peer in peers:
            try:
                peer.receive_commit(value)
            except Exception as e:
                logging.error(f"Error sending commit to node on port {peers}: {e}")

    def receive_commit(self, value):
        """Receive a commit message from another node."""
        logging.info(colored(f"Node on port {self.port} received commit for value: '{value}'", 'yellow'))
        self.update_file(value)

    def update_file(self, value):
        """Update the local CISC5597.txt file with the new value."""
        with open(self.file_path, 'w') as f:  # Append new value to the file
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Set value to: {value}\n")
        logging.info(colored(f"Node on port {self.port} updated file with value: '{value}'", 'green'))

    def prepare(self,n):
        global acceptedProposal, acceptedValue 
        logging.info(colored(f"STEP 3.1 - Received: Node received new proposal with proposal id: {n}", 'blue'))
        if self.minProposal is None or n >= self.minProposal:
            self.minProposal = n
            logging.info(colored(f"STEP 3.2 - Respond to Prepare: Setting minProposal to {n}", 'green'))
            self.promise =True
        else:
            logging.info(colored(f"STEP 3.2 - Respond to Prepare: Setting minProposal to {n}", 'green'))
        return acceptedProposal, acceptedValue, self.promise  # Accept the proposal

    def send_accept_with_delay(self, peer, proposal_num, value,delay,delay_sec):
        """Send a prepare message with an optional delay for testing."""
        if delay==1:
            time.sleep(delay_sec)
        return peer.accept(proposal_num,value)


    def propose_value(self, value,other_ports):
        # Generate a unique proposal ID based on the thread ID
        proposal_num = self.port
        self.peers = [xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}") for acceptor_port in other_ports]
        responses = []
        logging.info(colored(f"STEP 1: PREPARE({proposal_num})--> Node on port {self.port} preparing request with proposal id: {proposal_num}", 'blue'))
        for peer in self.peers:

            logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))
            logging.info(colored(f"STEP 2: Node on port {self.port} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
            try:
                acceptedProposal, acceptedValue, self.promise = peer.prepare(proposal_num)
                logging.info(colored(f"Step 4.1: Received Respond to Prepare({acceptedProposal})", 'blue'))
                if self.promise:
                    logging.info(colored(f"Step 4.2: acceptedValue: {acceptedValue} was returned in the response from {peer} with proposal ID: {acceptedProposal}", 'blue'))
                    responses.append([acceptedProposal,acceptedValue])
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {acceptedValue} was returned in the response from {peer} with proposal ID: {acceptedProposal}", 'blue'))
            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {peer}: {e}", "red"))
        if len(responses) <= 2:
            print("Failed to reach majority in Prepare phase.")
            return False


        highest_n = -1
        highest_value = None
        for accepted_n, accepted_value in responses:
            if accepted_n is not None and accepted_n > highest_n:
                highest_n = accepted_n
                highest_value = accepted_value
                agreed_value = highest_value if highest_value is not None else value
                logging.info(colored(f"Step 4: Node on port {self.port} using previously accepted value: {agreed_value} from highest proposal ID: {highest_n}", 'green'))

        agreed_value = highest_value if highest_value is not None else value
        accept_count = 0
        for peer in self.peers:
            try:
                logging.info(colored(f"STEP 5: Broadcast Accept({proposal_num}) to all servers", 'blue'))
                if peer.accept(proposal_num, agreed_value):
                    accept_count += 1
            except Exception:
                continue

        # Check for majority
        if accept_count >= len(self.peers) // 2 + 1:
            self.update_file(agreed_value)
            self.broadcast_commit(agreed_value,self.peers)
            logging.info(colored(f"Step 7: Node on port {self.port} consensus reached with value: {agreed_value}. Broadcasting commit.", 'blue'))
            print(f"Value '{agreed_value}' has been updated and committed.")
            return True
        else:
            print("Failed to reach consensus in Accept phase.")
            return False

    def propose_A(self,value,port,other_ports):
        global acceptedProposal, acceptedValue
        proposals = {}
        proposal_num = port
        self.other_ports = other_ports
        self.peers = [xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}",allow_none=True) for acceptor_port in other_ports]
        responses = 0
        logging.info(colored(f"STEP 1: PREPARE({proposal_num})--> Node on port {port} preparing request with proposal id: {proposal_num}", 'blue'))
        logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))
        for peer in self.peers:
            logging.info(colored(f"STEP 2: Node on port {port} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
            try:
                accepted_id, accepted_value,promise = peer.prepare(proposal_num)
                logging.info(colored(f"Step 4.1: Received Respond to Prepare({proposal_num})", 'blue'))
                if promise:
                    logging.info(colored(f"Step 4.2: acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                    responses +=1
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                if accepted_value:

                    proposals[accepted_id] = accepted_value
            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {peer}: {e}", "red"))

        if responses >= 2:
            if proposals:
                highest_proposal_id = max(proposals)
                with acceptedProposal_lock:
                    acceptedProposal = highest_proposal_id
                if highest_proposal_id is not None:
                    value = proposals[highest_proposal_id]
        else:
            print("Failed to reach majority in Prepare phase.")
            return False

        agreed_value = value
        logging.info(colored(f"Step 4: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))
        accept_count = 0
        for peer in self.peers:
            try:
                logging.info(colored(f"STEP 5: Broadcast Accept({proposal_num}) to all servers", 'blue'))
                if peer.accept(proposal_num, agreed_value):
                    accept_count += 1
            except Exception:
                continue

        if accept_count >= len(self.peers) // 2 + 1:
            self.update_file(agreed_value)
            self.broadcast_commit(agreed_value,self.peers)
            logging.info(colored(f"Step 7: Node on port {self.port} consensus reached with value: {agreed_value}. Broadcasting commit.", 'blue'))
            print(f"Value '{agreed_value}' has been updated and committed.")
            return True
        else:
            print("Failed to reach consensus in Accept phase.")
            return False

    def propose_B(self,value,port,other_ports,delay=None):
        global acceptedProposal, acceptedValue
        proposals = {}
        proposal_num = port
        self.other_ports = other_ports
        self.peers = [xmlrpc.client.ServerProxy(f"http://localhost:{acceptor_port}",allow_none=True) for acceptor_port in other_ports]
        responses = 0
        logging.info(colored(f"STEP 1: PREPARE({proposal_num})--> Node on port {port} preparing request with proposal id: {proposal_num}", 'blue'))
        logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))

        for peer in self.peers:
            logging.info(colored(f"STEP 2: Node on port {port} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
            try:
                accepted_id, accepted_value,promise = peer.prepare(proposal_num)
                logging.info(colored(f"Step 4.1: Received Respond to Prepare({proposal_num})", 'blue'))
                if promise:
                    logging.info(colored(f"Step 4.2: acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                    responses +=1
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                if accepted_value:

                    proposals[accepted_id] = accepted_value
            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {peer}: {e}", "red"))

        if responses >= 2:
            if proposals:
                highest_proposal_id = max(proposals)
                with acceptedProposal_lock:
                    acceptedProposal = highest_proposal_id
                if highest_proposal_id is not None:
                    value = proposals[highest_proposal_id]
        else:
            print("Failed to reach majority in Prepare phase.")
            return False

        agreed_value = value
        with acceptedValue_lock:
            acceptedValue = agreed_value
        # value = proposals[highest_proposal_id]  # Replace proposed value with the accepted value for highest accepted proposal ID

        accept_count = 0
        logging.info(colored(f"Step 4: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))
        with ThreadPoolExecutor() as executor:
            future_to_peer = {}
            for i, peer in enumerate(self.peers):
                print(f"Preparing {i} to send accept to peer {peer.port} with proposal_num: {proposal_num}, delay: {delay[i]}")
                future = executor.submit(self.send_accept_with_delay, peer, proposal_num, agreed_value, delay[i],1)
                future_to_peer[future] = peer
            logging.info(colored(f"STEP 5: Broadcast Accept({proposal_num}) to all servers", 'blue'))
            for future in as_completed(future_to_peer):
                peer = future_to_peer[future]
                try:
                    response = future.result()
                    if response:
                        peer.receive_commit(agreed_value)
                        accept_count += 1
                except Exception as e:
                    logging.error(colored(f"Error during accept phase with node {peer}: {e}", "red"))
        if accept_count >= 2:
            self.update_file(agreed_value)
            # self.broadcast_commit(agreed_value,self.peers)
            logging.info(colored(f"Step 7: Node on port {self.port} consensus reached with value: {agreed_value}. Broadcasting commit.", 'blue'))
            print(f"Value '{agreed_value}' has been updated and committed.")
            return True
        else:
            print("Failed to reach consensus in Accept phase.")
            return False


def run_server(port, other_ports):
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", port), allow_none=True)
    my_server = MyServer(port, other_ports)
    server.register_instance(my_server)
    logging.info(colored(f"Server running on port {port}...", 'green'))
    server.serve_forever()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python try1.py <port_number>")
        sys.exit(1)
    # Get the specified port from the command-line argument
    port = int(sys.argv[1])
    # Define all ports in the network
    all_ports = [8000, 8001, 8002,8003,8004]
    if port not in all_ports:
        print(f"\033[91m\nError: Invalid port {port}. Allowed ports are {all_ports}.\033[0m")
        sys.exit(1)

    # Determine the other ports for broadcasting
    other_ports = [p for p in all_ports if p != port]

    # Run the server on the specified port
    run_server(port, other_ports)
