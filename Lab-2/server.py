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

# Global variables
acceptedProposal = None
acceptedValue = None
acceptedProposal_lock = threading.Lock()
acceptedValue_lock = threading.Lock()

# Define server IPs and ports based on the node identifier
SERVER_IPS = {
    0: "10.128.0.10",
    1: "10.128.0.6",
    2: "10.128.0.7",
    3: "10.128.0.5",
    4: "10.128.0.9"
}
PORTS = [8000, 8001, 8002, 8003, 8004]

def get_ip_for_node(other_node_ids):
    # Map the other_node_id to an IP by modding it by the length of SERVER_IPS
    ip_list = []
    for other_node_id in other_node_ids:
        ip = SERVER_IPS[other_node_id % 10]
        ip_list.append(ip)
    return ip_list

def get_server_url(index, port_index):
    """Returns the server URL based on the port."""
    ip = SERVER_IPS.get(index, "localhost")
    port =PORTS.get(port_index,"8000")
    url = f"http://{ip}:{port}"
    return url
class MyServer:
    def __init__(self, node_id, other_node_ids):
        # node_id -> port
        #other_nodes -> other_nodes
        # self.port = port
        # self.other_nodes = None
        
        self.ip = SERVER_IPS[node_id]
        self.port = PORTS[node_id]
        self.node_id = node_id
        self.other_node_ids = None
        self.minProposal = None
        self.promise = False
        self.peers = None

        self.file_path = f"{self.port}/CISC5597.txt"
        os.makedirs(str(self.port), exist_ok=True)
        with open(self.file_path, 'w') as f:
            f.write("")

    def reset_file(self):
        """Clear the contents of the CISC5597.txt file."""
        with open(self.file_path, 'w') as f:
            f.write("")

    def restart(self):
        """Resets the state of the node to initial values."""
        global acceptedProposal, acceptedValue
        logging.info(colored(f"Restarting node on IP {self.ip} port {self.port}", 'yellow'))
        with acceptedProposal_lock:
            acceptedProposal = None
        with acceptedValue_lock:
            acceptedValue = None
        self.minProposal = None
        self.promise = False
        self.reset_file()
        logging.info(colored(f"Node on IP {self.ip}, port {self.port} has been reset.", 'green'))

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
        logging.info(colored(f"BROADCAST COMMIT: Node on IP {self.ip} port {self.port} broadcasting commit value: '{value}'", 'blue'))
        for peer in peers:
            try:
                peer.receive_commit(value)
            except Exception as e:
                logging.error(f"Error sending commit to peer {peer}: {e}")

    def receive_commit(self, value):
        """Receive a commit message from another node."""
        logging.info(colored(f"RECEIVED COMMIT REQ: Node on IP {self.ip} port {self.port} received commit for value: '{value}'", 'yellow'))
        self.update_file(value)

    def update_file(self, value):
        """Update the local CISC5597.txt file with the new value."""
        with open(self.file_path, 'w') as f:  # write new value to the file
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Set value to: {value}\n")
        logging.info(colored(f"UPDATE FILE: Node on IP {self.ip}, port {self.port} updated file with value: '{value}'", 'green'))

    def prepare(self,n):
        global acceptedProposal, acceptedValue 
        logging.info(colored(f"STEP 3.1: Received Prepare with proposal id: {n} at IP {self.ip}, port {self.port}", 'blue'))
        if self.minProposal is None or n >= self.minProposal:
            self.minProposal = n
            self.promise =True        
        logging.info(colored(f"STEP 3.2 - Respond to Prepare: Setting minProposal to {self.minProposal}", 'green'))
        return acceptedProposal, acceptedValue, self.promise

    def send_accept_with_delay(self, peer, proposal_num, value,delay,delay_sec):
        """Send a prepare message with an optional delay for testing."""
        if delay==1:
            time.sleep(delay_sec)
        return peer.accept(proposal_num,value)


    def propose_value(self, value, other_node_ids):
        # Generate a unique proposal ID based on the thread ID
        proposal_num = self.port
        self.peers = [
            xmlrpc.client.ServerProxy(f"http://{SERVER_IPS[other_id % 10]}:{PORTS[other_id % 10]}", allow_none=True)
            for other_id in other_node_ids
        ]
        responses = []
        logging.info(colored(f"STEP 1: PREPARE({proposal_num})--> Node on port {self.port} preparing request with proposal id: {proposal_num}", 'blue'))
        for peer in self.peers:
            try:
                logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))
                logging.info(colored(f"STEP 2: Node on port {self.ip} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))

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
            return "Failed to reach majority in Prepare phase."


        highest_n = -1
        highest_value = None
        agreed_value = None
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
            return f"Value '{agreed_value}' has been updated and committed."
        else:
            print("Failed to reach consensus in Accept phase.")
            return "Failed to reach consensus in Accept phase."

    def propose_A(self,value,node_id,other_node_ids):
        global acceptedProposal, acceptedValue
        proposals = {}
        proposal_num = node_id
        agreed_value = value

        self.other_nodes = other_node_ids
        self.peers = [
            xmlrpc.client.ServerProxy(f"http://{SERVER_IPS[other_id % 10]}:{PORTS[other_id % 10]}",allow_none=True)
            for other_id in other_node_ids
        ]
        responses = 0
        # Phase 1: Send Prepare to all nodes
        logging.info(colored(f"STEP 1: PREPARE({proposal_num}) --> Node on IP {self.ip} port {self.port}", 'blue'))
        for peer in self.peers:
            logging.info(colored(f"STEP 2: Node on port {self.ip} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
            try:
                accepted_id, accepted_value,promise = peer.prepare(proposal_num)
                logging.info(colored(f"Step 4.1: Received Respond to Prepare({proposal_num})", 'blue'))
                if promise:
                    logging.info(colored(f"Step 4.2: acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                    responses +=1
                if accepted_value:
                    proposals[accepted_id] = accepted_value
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))

            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {peer}: {e}", "red"))

        if responses >= 2:
            if proposals:
                highest_proposal_id = max(proposals)
                with acceptedProposal_lock:
                    acceptedProposal = highest_proposal_id
                if highest_proposal_id is not None:
                    agreed_value = proposals[highest_proposal_id]
                    logging.info(colored(f"Step 5: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))

        else:
            print("Failed to reach majority in Prepare phase.")
            return "Failed to reach majority in Prepare phase."

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
            return f"Value '{agreed_value}' has been updated and committed."
        else:
            print("Failed to reach consensus in Accept phase.")
            return "Failed to reach consensus in Accept phase."

    def propose_B(self,value,node_id,other_node_ids,delay=None):
        global acceptedProposal, acceptedValue
        proposals = {}
        proposal_num = node_id
        agreed_value = value

        self.other_nodes = other_node_ids
        self.peers = [
            xmlrpc.client.ServerProxy(f"http://{SERVER_IPS[other_id % 10]}:{PORTS[other_id % 10]}",allow_none=True)
            for other_id in other_node_ids
        ]
        responses = 0
        logging.info(colored(f"STEP 1: PREPARE({proposal_num}) --> Node on IP {self.ip} port {self.port}", 'blue'))

        for peer in self.peers:
            logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))
            logging.info(colored(f"STEP 2: Node on port {self.ip} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
            try:
                accepted_id, accepted_value,promise = peer.prepare(proposal_num)
                logging.info(colored(f"Step 4.1: Received Respond to Prepare({proposal_num})", 'blue'))
                if promise:
                    logging.info(colored(f"Step 4.2: acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                    responses +=1
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))
                if accepted_value:
                    proposals[accepted_id] = accepted_value
                    logging.info(colored(f"Step 4.3: Replaced 'value' with acceptedValue for highest acceptedValue: {accepted_value} was returned in the response from {peer} with proposal ID: {accepted_id}", 'blue'))

            except Exception as e:
                logging.error(colored(f"Error during prepare phase with node {peer}: {e}", "red"))

        if responses >= 2:
            if proposals:
                highest_proposal_id = max(proposals)
                with acceptedProposal_lock:
                    acceptedProposal = highest_proposal_id
                if highest_proposal_id is not None:
                    agreed_value = proposals[highest_proposal_id]
                    logging.info(colored(f"Step 5: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))
        else:
            print("Failed to reach majority in Prepare phase.")
            return False

        with acceptedValue_lock:
            acceptedValue = agreed_value
        # value = proposals[highest_proposal_id]  # Replace proposed value with the accepted value for highest accepted proposal ID

        accept_count = 0
        logging.info(colored(f"Step 4: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))
        with ThreadPoolExecutor() as executor:
            future_to_peer = {}
            for i, peer in enumerate(self.peers):
                print(f"Preparing {i} to send accept to peer {peer} with proposal_num: {proposal_num}, delay: {delay[i]}")
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
        
        self.update_file(agreed_value)
        if accept_count >= 2:
            # self.broadcast_commit(agreed_value,self.peers)
            logging.info(colored(f"Step 7: Node on port {self.port} consensus reached with value: {agreed_value}. Broadcasting commit.", 'blue'))
            print(f"Value '{agreed_value}' has been updated and committed.")
            return f"Value '{agreed_value}' has been updated and committed."
        else:
            print("Failed to reach consensus in Accept phase.")
            return False
    
    def propose_livelock(self,value,proposal_num,node_id,other_node_ids,delay=None):
        global acceptedProposal, acceptedValue
        proposals = {}
        proposal_num = proposal_num
        self.other_node_ids = other_node_ids
        self.peers = [
            xmlrpc.client.ServerProxy(f"http://{SERVER_IPS[other_id % 10]}:{PORTS[other_id % 10]}",allow_none=True)
            for other_id in other_node_ids
        ]
        agreed_value = value
        responses = 0
        logging.info(colored(f"STEP 1: PREPARE({proposal_num})--> Node on port {self.ip} preparing request with proposal id: {proposal_num}", 'blue'))
        logging.info(colored(f"STEP 2: Broadcast Prepare({proposal_num}) to all servers", 'blue'))

        for peer in self.peers:
            logging.info(colored(f"STEP 2: Node on port {self.ip} send Prepare({proposal_num}) to node at port: {peer}", 'cyan'))
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
                    agreed_value = proposals[highest_proposal_id]
        else:
            print("Failed to reach majority in Prepare phase.")
            return False

        
        with acceptedValue_lock:
            acceptedValue = agreed_value
        # value = proposals[highest_proposal_id]  # Replace proposed value with the accepted value for highest accepted proposal ID

        accept_count = 0
        logging.info(colored(f"Step 4: Node on port {self} using previously accepted value: {agreed_value} ", 'green'))
        with ThreadPoolExecutor() as executor:
            future_to_peer = {}
            for i, peer in enumerate(self.peers):
                print(f"Preparing {i} to send accept to peer {peer.port} with proposal_num: {proposal_num}, delay: {delay[i]}")
                future = executor.submit(self.send_accept_with_delay, peer, proposal_num, agreed_value, delay[i],5)
                future_to_peer[future] = peer
            logging.info(colored(f"STEP 5: Broadcast Accept({proposal_num}) to all servers", 'blue'))
            for future in as_completed(future_to_peer):
                peer = future_to_peer[future]
                try:
                    response = future.result()
                    if response:
                        self.update_file(value)
                        # peer.receive_commit(agreed_value)
                        accept_count += 1
                except Exception as e:
                    logging.error(colored(f"Error during accept phase with node {peer}: {e}", "red"))
        if accept_count >= 2:
            self.update_file(agreed_value)
            print(f"Value '{agreed_value}' has been updated and committed.")
            return True
        else:
            print("Failed to reach consensus in Accept phase.")
            return False


def run_server(node_id, other_node_ids):
    server = xmlrpc.server.SimpleXMLRPCServer((SERVER_IPS[node_id], PORTS[node_id]), allow_none=True)
    my_server = MyServer(node_id, other_node_ids)
    server.register_instance(my_server)
    logging.info(colored(f"Server started at {SERVER_IPS[node_id]}:{PORTS[node_id]}", 'green'))
    server.serve_forever()



if __name__ == "__main__":
    node_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    other_node_ids = [i for i in range(5) if i != node_id]
    run_server(node_id, other_node_ids)

