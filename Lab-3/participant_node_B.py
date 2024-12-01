from xmlrpc.server import SimpleXMLRPCServer
import os
import logging
import time
import re

from termcolor import colored  # For colored logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
def read_account(file_name):
    with open(file_name, 'r') as file:
        return float(file.read().strip())

def write_account(file_name, value):
    with open(file_name, 'w') as file:
        file.write(f"{value:.2f}\n")

class ParticipantB:
    def __init__(self):
        self.account_file = "account_B.txt"
        self.LOG_FILE = "account_B_log.txt"
        self.temp_file = self.account_file + ".tmp"
        self.prepared = False
        self.scenario_number = None
        self.transaction_number = None
        self.balance = None
        self.crash_before = False
        self.crash_after = False

        with open("account_B.txt", "w") as file_B:
            file_B.write(str('0.0'))

        with open(self.LOG_FILE, "w") as file_B_log:
            file_B_log.write(str(f'Log of Node B: \n\n'))

    def log_action(self, action, scenario, transaction, amount=None ):
        with open(self.LOG_FILE, "a") as LOG_FILE:
            LOG_FILE.write(f"\n\n{action} {scenario} {transaction} {amount}")
                           
    def canCommit(self, transaction_number):
        self.transcation_number = transaction_number

        if not os.path.exists(self.account_file):
            self.prepared = False
            self.log_action("Vote NO", self.scenario_number, transaction_number)      
            logging.info(colored(f"Account B does not exists", 'red'))                   
        else:
            self.prepared = True
            self.balance = float(read_account(self.account_file))
            self.log_action("Vote YES", self.scenario_number, transaction_number)                          
            logging.info(colored(f"Account B exists and balance is {self.balance}", 'green'))                
        
    
        # Simulate a delay/crash for Node-B.
        if self.crash_before:  # Simulate crash for Node-2
            logging.warning(colored(f"Simulating crash for Transaction:{self.transcation_number} simulating a crash (long sleep)...", 'yellow'))
            time.sleep(10)  # Simulate long sleep to represent crash
            
        try:
            last_command = self.get_last_command()  # Get the last command from the log
            if self.crash_before:
                if last_command.startswith('Vote'):
                    self.abort()           
                self.crash_before = False
            return self.prepared
        except Exception as e:
            self.log_action("Vote NO", self.scenario_number, transaction_number)      
            logging.error(colored(f"Error during canCommit for: {str(e)}", 'red'))     

    def doCommit(self, transaction_number, increment = None):
        self.transcation_number = transaction_number
        # Simulate a delay/crash for Node-B.
        if self.crash_after:  # Simulate crash for Node-2
            logging.warning(colored(f"Simulating crash for Transaction:{self.transcation_number} simulating a crash (long sleep)...", 'yellow'))
            time.sleep(10)  # Simulate long sleep to represent crash
            # self.crash_after = False

        try:
            last_command = self.get_last_command()
            if last_command.startswith('Vote'):
                if self.crash_after:
                    self.abort()
                    self.crash_after = False
                else:
                    if self.transcation_number == 1:
                        new_balance = self.balance + 100
                        write_account(self.account_file, new_balance)
                        logging.info(colored(f"Account B updated value from {self.balance} to {new_balance} after Transaction {self.transcation_number}", 'green'))
                        self.log_action("COMMITED YES", self.scenario_number, transaction_number, +100.00)
                        self.balance = new_balance
                        self.commit_status = True                        

                    elif self.transcation_number == 2:
                        new_balance = self.balance + increment
                        write_account(self.account_file, new_balance)
                        self.log_action("COMMITED YES", self.scenario_number, transaction_number, increment)
                        self.balance = new_balance
                        self.commit_status = True
                        logging.info(colored(f"Account B increment value by {increment} after Transaction {self.transcation_number}", 'green'))
                        logging.info(colored(f"Account B new balance: {self.balance}", 'green'))
                    else:
                        self.log_action("COMMITED NO", self.scenario_number, transaction_number)
                        logging.info(colored(f"Invlaid transaction {transaction_number} ", 'red'))
                    return self.commit_status
           
        except Exception as e:
            self.log_action("COMMITED NO", self.scenario_number, transaction_number)
            logging.error(colored(f"Error during commit: {str(e)}", 'red'))  

    def initialize_account(self, scenario_number):
        """
        Set the initial value of the account based on the scenario number.
        """
        print("****** scenario number",scenario_number)
        self.scenario_number = scenario_number
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
    
    def get_last_command(self):
            try:
                # Open the log file
                with open(self.LOG_FILE, 'r') as log_file:
                    # Read the last line from the file
                    lines = log_file.readlines()
                    if not lines:
                        return None  # File is empty

                    last_line = lines[-1].strip()
                    return last_line  # Return the last line as the command

            except Exception as e:
                print(f"Error reading the log file: {e}")
                return None

    def get_last_commit_value(self, starts_with):
        try:
            last_command = self.get_last_command()  # Get the last command from the log
            if last_command and last_command.startswith(starts_with):
                # Use regular expression to find the last float number
                match = re.search(r"([+-]?\d+\.\d+)$", last_command)
                if match:
                    # Extract and return the float value
                    return float(match.group(1))
                else:
                    return None  # No float found at the end of the line
            else:
                return None  # Line does not start with the specified prefix

        except Exception as e:
            print(f"Error reading the log file: {e}")
            return None

    def abort(self, revert=False):
        if revert:
            value = self.get_last_commit_value("COMMITED YES")
            if value is not None:
                print(f"Extracted value: {value}")
            else:
                print("No valid 'COMMITTED YES' log found or error reading the log.")

            print(self.balance,"/*/**/*****/*",value)  # Output: 20.0
            write_account(self.account_file, self.balance - value)
        self.prepared = False
        self.log_action("ABORT", self.scenario_number, self.transaction_number)
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
