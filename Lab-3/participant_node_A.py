import re
from xmlrpc.server import SimpleXMLRPCServer
import os
import logging
from termcolor import colored  # For colored logging



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def read_account(file_name):
    with open(file_name, 'r') as file:
        return float(file.read().strip())

def write_account(file_name, value):
    logging.info(colored(f"writing {file_name}, {value}", 'green'))
    with open(file_name, 'w') as file:
        file.write(f"{value:.2f}\n")

class ParticipantA:
    def __init__(self):
        self.account_file = "account_A.txt"
        self.LOG_FILE = "account_A_log.txt"
        self.temp_file = self.account_file + ".tmp"
        self.prepared = False
        self.scenario_number = None
        self.transaction_number = None
        self.balance = None
        self.commit_status = False

        with open(self.account_file, "w") as file_A:
            file_A.write(str('0.0'))

        with open(self.LOG_FILE, "w") as file_A_log:
            file_A_log.write(str(f'Log of Node A: \n\n'))
            
    def log_action(self, action, scenario, transaction, amount=None ):
        with open(self.LOG_FILE, "a") as LOG_FILE:
            LOG_FILE.write(f"\n\n{action} {scenario} {transaction} {amount}")
    
    def canCommit(self, transaction_number):
        self.transcation_number = transaction_number
        try:
            logging.info(colored(f"CAN COMMIT:", 'yellow'))
            if not os.path.exists(self.account_file):
                self.prepared = False
                self.log_action("Vote NO", self.scenario_number, transaction_number)   
                logging.info(colored(f"Account A does not exists", 'red'))
                return self.prepared
            else:
                self.balance = float(read_account(self.account_file))
                if self.transcation_number == 1:                                    
                    # Simulate the operation: subtract $100 and add 20% bonus
                    if self.balance >= 100:
                        logging.info(colored(f"Account A exists and balance {self.balance} > 100", 'green'))                
                        self.prepared = True
                        self.log_action("Vote YES", self.scenario_number, transaction_number)                          
                    else:    
                        logging.info(colored(f"Account A exists and balance {self.balance} < 100", 'red'))
                        self.prepared = False
                        self.log_action("Vote NO", self.scenario_number, transaction_number) 
                    return self.prepared   
                elif self.transcation_number == 2:
                    if self.balance > 0:
                        logging.info(colored(f"Account A exists and balance {self.balance} > 0", 'green'))                
                        self.prepared = True
                        self.log_action("Vote YES", self.scenario_number, transaction_number)
                    else:
                        self.log_action("Vote NO", self.scenario_number, transaction_number)    
                        logging.info(colored(f"Account A exists and balance {self.balance} <=0", 'red'))
                    return self.prepared      
                else:
                    self.log_action("Vote NO", self.scenario_number, transaction_number)
                    logging.info(colored(f"Account A exists but the transaction id is not valid", 'red'))
                    return False
                
        except Exception as e:
            self.log_action("Vote NO", self.scenario_number, transaction_number)
            logging.error(colored(f"Error during canCommit for: {str(e)}", 'red'))     
        
    
    def doCommit(self, transaction_number):
        self.transcation_number = transaction_number
        increment = None
        try:
            if self.transcation_number == 1:
                new_balance = self.balance - 100
                write_account(self.account_file, new_balance)
                logging.info(colored(f"Account A updated value from {self.balance} to {new_balance} after Transaction {self.transcation_number}", 'green'))
                self.log_action("COMMITED YES", self.scenario_number, transaction_number, -100.00)
                self.balance = new_balance
                self.commit_status = True
        

            elif self.transcation_number == 2:
                increment = 0.2 * self.balance
                new_balance = self.balance + increment
                write_account(self.account_file, new_balance)
                self.log_action("COMMITED YES", self.scenario_number, transaction_number, increment)
                self.balance = new_balance
                self.commit_status = True
                logging.info(colored(f"Account A increment value by {increment} after Transaction {self.transcation_number}", 'green'))
                logging.info(colored(f"Account A new balance: {self.balance}", 'green'))
            
            else:
                self.log_action("COMMITED NO", self.scenario_number, transaction_number)
                logging.info(colored(f"Invlaid transaction {transaction_number} ", 'red'))
            return self.commit_status, increment
        
        except Exception as e:
            self.log_action("COMMITED NO", self.scenario_number, transaction_number)
            logging.error(colored(f"Error during commit: {str(e)}", 'red'))  

    def initialize_account(self, scenario_number):
        """
        Set the initial value of the account based on the scenario number.
        """
        self.scenario_number = scenario_number
        if scenario_number == 2:
            self.balance = 90.0
        else:
            self.balance = 200.0
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

        if os.path.exists(self.account_file):
            with open(self.account_file, 'w') as file:
                file.write(f"{self.balance:.2f}")       

        logging.info(colored("Participant state reset successfully.", 'blue'))
        return "Participant A state reset successfully."
    
def main():
    participant = ParticipantA()
    with SimpleXMLRPCServer(("localhost", 8002),allow_none=True) as server:
        server.register_instance(participant)
        print("Participant A ready on port 8002...")
        logging.info(colored(f"Participant Server started at http://localhost:8002", 'green'))

        server.serve_forever()

if __name__ == "__main__":
    main()
