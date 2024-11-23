from xmlrpc.server import SimpleXMLRPCServer
import os
import logging
import time

from termcolor import colored  # For colored logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_account(file_name):
    with open(file_name, 'r') as file:
        return float(file.read().strip())

def write_account(file_name, value):
    with open(file_name, 'w') as file:
        file.write(f"{value:.2f}")

class ParticipantB:
    def __init__(self):
        self.account_file = "account_B.txt"
        self.temp_file = self.account_file + ".tmp"
        self.prepared = False
        self.transcation_number = None
        self.balance = None
        self.crash_before = False
        self.crash_after = False

        with open("account_B.txt", "w") as file_B:
            file_B.write(str('0.0'))
            
    def canCommit(self, transaction_number):
        self.transcation_number = transaction_number

        # Simulate a delay/crash for Node-B.
        if self.crash_before:  # Simulate crash for Node-2
            logging.warning(colored(f"Simulating crash for Transaction:{self.transcation_number} simulating a crash (long sleep)...", 'yellow'))
            time.sleep(20)  # Simulate long sleep to represent crash
            self.crash_before = False
        try:
            # Check if self.file exists
            if not os.path.exists(self.account_file):
                self.prepared = False   
                logging.info(colored(f"Account B does not exists", 'red'))        
            else:
                self.prepared = True
                self.balance = float(read_account(self.account_file))
                logging.info(colored(f"Account B exists and balance is {self.balance}", 'green'))                
            return self.prepared   
        
        except Exception as e:
            logging.error(colored(f"Error during canCommit for: {str(e)}", 'red'))     

    def doCommit(self, transaction_number, increment = None):
        self.transcation_number = transaction_number
        print("/*/*/**/*/*/****/*/**", self.crash_after)
        # Simulate a delay/crash for Node-B.
        if self.crash_after:  # Simulate crash for Node-2
            logging.warning(colored(f"Simulating crash for Transaction:{self.transcation_number} simulating a crash (long sleep)...", 'yellow'))
            time.sleep(10)  # Simulate long sleep to represent crash
            self.crash_after = False

        try:
            if self.transcation_number == 1:
                new_balance = self.balance + 100
                write_account(self.account_file, new_balance)
                logging.info(colored(f"Account B updated value from {self.balance} to {new_balance} after Transaction {self.transcation_number}", 'green'))

                self.balance = new_balance
                self.commit_status = True                        

            elif self.transcation_number == 2:
                new_balance = self.balance + increment
                write_account(self.account_file, new_balance)
                self.balance = new_balance
                self.commit_status = True
                logging.info(colored(f"Account B increment value by {increment} after Transaction {self.transcation_number}", 'green'))
                logging.info(colored(f"Account B new balance: {self.balance}", 'green'))
            else:
                logging.info(colored(f"Invlaid transaction {transaction_number} ", 'red'))
            return self.commit_status
        
        except Exception as e:
            logging.error(colored(f"Error during commit: {str(e)}", 'red'))  


    # def prepare(self):
    #     try:
    #         balance = float(read_account(self.account_file))
    #         # Simulate the operation: add $100 and 20% of A's balance
    #         new_balance = balance + 100 + (0.2 * int(read_account("account_A.txt")))
    #         write_account(self.temp_file, new_balance)
    #         self.prepared = True
    #         return "PREPARED"
    #     except Exception as e:
    #         return f"ERROR: {str(e)}"

    # def commit(self):
    #     if self.prepared and os.path.exists(self.temp_file):
    #         os.replace(self.temp_file, self.account_file)
    #         self.prepared = False
    #         return "COMMITTED"
    #     return "NOT PREPARED"

    def initialize_account(self, scenario_number):
        """
        Set the initial value of the account based on the scenario number.
        """
        print("****** scenario number",scenario_number)
        if scenario_number == 2:
            self.balance = 50.0
        else:
            self.balance = 300.0
            if scenario_number == 3:
                self.crash_before = True
            elif scenario_number == 4:
                self.crash_after = True
        try:
            write_account(self.account_file, self.balance)
            logging.info(colored(f"Account initialized with {self.balance} for Scenario {scenario_number}.", 'blue'))
            return True
        except Exception as e:
            logging.error(colored(f"Error initializing account: {e}", 'red'))
            return False
    
    def abort(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        self.prepared = False
        logging.info(colored(f"ABORTED !!!.", 'red'))
        return "ABORTED"

    def restart(self):
        """Reset the participant's state to its initial configuration."""
        self.prepared = False
        self.transaction_number = None
        self.balance = 0.0
        self.commit_status = False
        self.crash_before = False
        self.crash_after = False

        if os.path.exists(self.account_file):
            with open(self.account_file, 'w') as file:
                file.write(f"{self.balance:.2f}")  

        logging.info(colored("Participant state reset successfully.", 'blue'))
        return "Participant B state reset successfully."
    
def main():
    participant = ParticipantB()
    with SimpleXMLRPCServer(("localhost", 8003),allow_none=True) as server:
        server.register_instance(participant)
        print("Participant B ready on port 8003...")
        logging.info(colored(f"Participant Server started at http://localhost:8003", 'green'))
        server.serve_forever()

if __name__ == "__main__":
    main()
