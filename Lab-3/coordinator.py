from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import logging
from termcolor import colored  # For colored logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define server IPs and ports based on the node identifier
SERVER_IPS = {
    0: "10.128.0.10",
    1: "10.128.0.6",
    2: "10.128.0.7",
    3: "10.128.0.5",
    4: "10.128.0.9"
}
PORTS = [8000, 8001, 8002, 8003, 8004]

class Coordinator:
    def __init__(self, participant_1, participant_2):
        self.participant_1 = ServerProxy(participant_1, allow_none=True)
        self.participant_2 = ServerProxy(participant_2,allow_none=True)
        self.transaction_number = None

    def doCommitOnNode(self, participant, transaction_number):
        """Attempt to commit for a participant."""
        try:
            logging.info(colored(f"Attempting to commit on", 'blue'))
            A_commit_status, increment = participant.doCommit(transaction_number)
            print("*------*--*---", A_commit_status, increment)
            logging.info(colored(f"Attempting to commit on {participant}", 'blue'))
            B_commit_status = participant.doCommit(transaction_number, increment)

            if A_commit_status and B_commit_status:
                logging.info(colored("Transaction Committed Successfully to node A and B", 'green'))
                return True
            else:
                self.abort_transaction()
                logging.info(colored("Transaction Aborted on node A and B", 'red'))
                return False
        except Exception as e:
            logging.error(colored(f"Error during commit transaction: {str(e)}", 'red'))
        
    def abort_transaction(self):
        """Abort transaction for all participants."""
        logging.warning(colored("Aborting transaction for all participants", 'red'))
        try:
            self.participant_1.abort()
        except Exception as e:
            logging.error(colored(f"Error aborting transaction on node A: {str(e)}", 'red'))

        try:
            self.participant_2.abort()
        except Exception as e:
            logging.error(colored(f"Error aborting transaction on node B: {str(e)}", 'red'))    

    def canNodesCommit(self, participant,transaction_number):
        """Check if a participant can commit."""
        try:
            logging.info(colored(f"Checking if {participant} can commit", 'yellow'))
            return participant.canCommit(transaction_number)
        except Exception as e:
            logging.error(colored(f"Error during canCommit for {participant}: {str(e)}", 'red'))
            return False
        
    def commitPhase(self,transaction_number):
        # Commit Phase
        """Check if a participant can commit."""
        try:
            logging.info(colored(f"Attempting to commit on Node A", 'blue'))
            A_commit_status, increment  = self.participant_1.doCommit(transaction_number)
            print("*------*--*---", A_commit_status, increment)
            logging.info(colored(f"Attempting to commit on Node B", 'blue'))
            B_commit_status = self.participant_2.doCommit(transaction_number, increment)

            if A_commit_status and B_commit_status:
                logging.info(colored("Transaction Committed Successfully to node A and B", 'green'))
                return True
            else:
                logging.info(colored("Error during commit phase:", 'red'))
                return False
        except Exception as e:
            logging.error(colored(f"Error during commit transaction: {str(e)}", 'red'))
        
        
    def preparePhase(self,transaction_number):
        # Prepare Phase
        """Check if a participant can commit."""
        try:
            logging.info(colored(f"Checking if participant A can commit", 'yellow'))
            canAcommit = self.canNodesCommit(self.participant_1,transaction_number)
            logging.info(colored(f"Checking if participant B can commit", 'yellow'))
            canBcommit = self.canNodesCommit(self.participant_2,transaction_number)

            if canAcommit and canBcommit:
                return True
            else:
                return False
            
        except Exception as e:
            logging.error(colored(f"Error during prepare phase: {str(e)}", 'red'))
            return False        

    def execute_transaction(self,transaction_number):
        """Execute the distributed transaction."""
        self.transaction_number = transaction_number
        try:
            # Prepare Phase
            logging.info(colored("Prepare Phase Initiated", 'green'))
            canCommit = self.preparePhase( self.transaction_number)
            logging.info(colored("Prepare Phase Completed ", 'green'))

            # Commit Phase
            if canCommit:
                logging.info(colored("Commit Phase Initiated", 'green'))
                doCommitStatus = self.commitPhase( self.transaction_number)               

                if doCommitStatus:
                    logging.info(colored("Transaction Committed Successfully to node A and B", 'green'))    
                    return f"Transaction {transaction_number} Committed Successfully", True
                else:                    
                    return "Transaction{self.transaction_number} Failed", False
            else:
                logging.info(colored("Transaction Aborted Initiated on node A and B", 'red'))
                self.abort_transaction()
                return "Transaction Aborted", False

        except Exception as e:
            self.abort_transaction()
            logging.error(colored(f"Transaction Failed: {str(e)}", 'red'))
            
    
    
def main():
    coordinator = Coordinator("http://localhost:8002", "http://localhost:8003")
    with SimpleXMLRPCServer(("localhost", 8001)) as server:
        server.register_instance(coordinator)
        print("Coordinator ready on port 8001...")
        logging.info(colored(f"Coordinator Server started at http://localhost:8001", 'green'))
        server.serve_forever()

if __name__ == "__main__":
    main()
