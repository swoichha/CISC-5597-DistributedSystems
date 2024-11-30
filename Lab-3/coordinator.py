from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import logging
from termcolor import colored  # For colored logging
import sys
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Coordinator:
    def __init__(self, participant_1, participant_2):
        self.participant_1 = ServerProxy(participant_1, allow_none=True)
        self.participant_2 = ServerProxy(participant_2,allow_none=True)
        self.transaction_number = None
        self.scenario_number = None
        self.initialized_scenarios = set()  # Tracks initialized scenarios
        self.LOG_FILE = "coordinator_log.txt"

        with open(self.LOG_FILE, "w") as file_coordinator_log:
            file_coordinator_log.write(str(f'Log of Coordinator:\n'))

    def log_action(self, action, scenario, transaction):
        with open(self.LOG_FILE, "a") as LOG_FILE:
            LOG_FILE.write(f"{action} {scenario} {transaction}\n\n")
        return
    def abort_transaction(self):
        """Abort transaction for all participants."""
        self.log_action("ABORT", self.scenario_number, self.transaction_number)
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
        participant_name = "Participant A" if participant == self.participant_1 else "Participant B"
        try:
            logging.info(colored(f"Checking if {participant_name} can commit", 'yellow'))
            can_commit = participant.canCommit( transaction_number)
            
            if can_commit:
                logging.info(colored(f"{participant_name} agreed to commit.", 'green'))
            else:
                logging.info(colored(f"{participant_name} cannot commit.", 'red'))
                
            return can_commit
        except Exception as e:
            logging.error(colored(f"Error during canCommit for {participant_name}: {str(e)}", 'red'))
            return False
        
    def commitPhase(self,transaction_number):
        
        # Commit Phase
        """Check if a participant can commit."""
        try:
            logging.info(colored(f"Attempting to commit on Node A", 'blue'))
            A_commit_status, increment  = self.participant_1.doCommit(transaction_number)
            print("*------*--*---", A_commit_status, increment)
            logging.info(colored(f"Attempting to commit on Node B", 'blue'))
            
            # Simulate crash for Node B (after voting to commit, but before actually committing)
            response_B = [None]  # Use a list to capture response from thread
            
            def commit_node_b():
                # Participant B tries to commit
                response_B[0] = self.participant_2.doCommit(transaction_number, increment)
            
            # Start the thread to wait for Node-B's response
            thread_B = threading.Thread(target=commit_node_b)
            thread_B.start()
            thread_B.join(timeout=5)  # Wait for up to 5 seconds for Node B to commit


            if response_B[0] is None:  # Timeout occurred (simulating crash of Node B)
                logging.error(colored("Timeout waiting for Node B's commit. Assuming crash.", 'red'))
                # Simulate that Node B crashed, and abort the transaction
                self.abort_transaction()
                return False  # Return false indicating the transaction failed
        
            # If Node B commits successfully
            if A_commit_status and response_B[0]:
                self.log_action("Committed YES", self.scenario_number, self.transaction_number)
                logging.info(colored("Transaction Committed Successfully to Node A and B", 'green'))
                return True
            else:
                self.log_action("Committed NO", self.scenario_number, self.transaction_number)
                logging.error(colored("Error during commit phase.", 'red'))
                return False
            
        except Exception as e:
            logging.error(colored(f"Error during commit transaction: {str(e)}", 'red'))
            logging.error(colored("Simulated crash for Node B. Aborting transaction.", 'red'))
            self.abort_transaction()  # Abort transaction on both nodes
            return False

        
    def preparePhase(self,transaction_number):
        # Prepare Phase
        """Check if a participant can commit."""
        
        try:
            logging.info(colored(f"Checking if participant A can commit", 'yellow'))
            canAcommit = self.canNodesCommit(self.participant_1,transaction_number)
            # Step 1: Check Node-A
            if not canAcommit:
                self.log_action("Node A preparePhase NO", self.scenario_number, self.transaction_number)
                logging.warning(colored("Node-A cannot commit. Aborting transaction.", 'red'))
                return False
            
            # Step 2: Check Node-B with timeout          
            logging.info(colored(f"Checking if participant B can commit", 'yellow'))
            response_B = [None]  # Use a list to capture response from thread

            def check_node_b():
                response_B[0] = self.canNodesCommit(self.participant_2, transaction_number)

            # Start the thread to wait for Node-B's response
            thread = threading.Thread(target=check_node_b)
            thread.start()
            thread.join(timeout=5)  # Wait for up to 5 seconds

            if response_B[0] is None:  # Timeout occurred
                self.log_action("Node A preparePhase NO", self.scenario_number, self.transaction_number)
                logging.error(colored("Timeout waiting for Node-B's response. Aborting transaction.", 'red'))
                return False  # Or handle it as you wish (e.g., partial commit, abort, etc.)
            elif not response_B[0]:  # Node-B explicitly cannot commit
                self.log_action("Node A preparePhase NO", self.scenario_number, self.transaction_number)
                logging.warning(colored("Node-B cannot commit. Aborting transaction.", 'red'))
                return False

            # If both nodes can commit
            return True
            
        except Exception as e:
            logging.error(colored(f"Error during prepare phase: {str(e)}", 'red'))
            return False        

    def execute_transaction(self, scenario_number,transaction_number):
        """Execute the distributed transaction."""
        self.transaction_number = transaction_number
        self.scenario_number = scenario_number
        try:
            # Initialize accounts only if this scenario hasn't been initialized
            if scenario_number not in self.initialized_scenarios:
                initialize_val_A = self.participant_1.initialize_account(self.scenario_number)
                initialize_val_B = self.participant_2.initialize_account(self.scenario_number)

                if initialize_val_A and initialize_val_B:
                    self.initialized_scenarios.add(scenario_number)
                    self.log_action("Accounts initialized for scenario", self.scenario_number, self.transaction_number)
                    logging.info(colored(f"Accounts initialized for scenario {scenario_number}.", 'green'))
                else:
                    self.log_action("Failed to initialize account for scenario", self.scenario_number, self.transaction_number)
                    logging.error(colored(f"Failed to initialize accounts for scenario {scenario_number}.", 'red'))
                    return f"Error during initializing values for scenario {scenario_number}.", False
            else:
                logging.info(colored(f"Scenario {scenario_number} already initialized. Skipping initialization.", 'yellow'))


        except Exception as e:
            logging.error(colored(f"Error during initializing value for scenario {self.scenario_number} before starting 2PC: {str(e)}", 'red'))
            return f"Error during initializing value for scenario {self.scenario_number} before starting 2PC: {str(e)}",False
        
        try:
            # Prepare Phase
            logging.info(colored("Prepare Phase Initiated", 'green'))
            canCommit = self.preparePhase(self.transaction_number)  # Timeout set to 10 seconds            

            # Commit Phase
            if canCommit:
                self.log_action("Prepare Phase Successfully Completed", self.scenario_number, self.transaction_number)
                logging.info(colored("Prepare Phase Successfully Completed ", 'green'))
                logging.info(colored("Commit Phase Initiated", 'green'))
                doCommitStatus = self.commitPhase( self.transaction_number)               

                if doCommitStatus:
                    logging.info(colored("Transaction Committed Successfully to node A and B", 'green'))    
                    return f"Transaction Committed Successfully", True
                else:                    
                    return "Transaction Failed", False
            else:
                logging.error(colored("Transaction Aborted Initiated on node A and B", 'red'))
                self.abort_transaction()
                return "Transaction Aborted", False

        except Exception as e:
            self.abort_transaction()
            logging.error(colored(f"Transaction Failed: {str(e)}", 'red'))
            return "Transaction Aborted", False
        
    def restart(self):
        """Reset the coordinator's state and all participants."""
        self.transaction_number = None
        self.scenario_number = None
        self.initialized_scenarios.clear()  # Clear the initialized scenarios set

        try:
            logging.info(colored("Resetting Participant A...", 'blue'))
            restart_A = self.participant_1.restart()
            logging.info(colored(f"{restart_A}", 'blue'))

            logging.info(colored("Resetting Participant B...", 'blue'))
            restart_B = self.participant_2.restart()
            logging.info(colored(f"{restart_B}", 'blue'))

            logging.info(colored("Coordinator and Participants state reset successfully.", 'green'))
            return "Coordinator and Participants state reset successfully.", True
        except Exception as e:
            logging.error(colored(f"Error during restart: {str(e)}", 'red'))
            return f"Error during restart: {str(e)}", False

    
def main():
    coordinator = Coordinator("http://localhost:8002", "http://localhost:8003")
    with SimpleXMLRPCServer(("localhost", 8001)) as server:
        server.register_instance(coordinator)
        print("Coordinator ready on port 8001...")
        logging.info(colored(f"Coordinator Server started at http://localhost:8001", 'green'))
        server.serve_forever()

if __name__ == "__main__":
    main()
