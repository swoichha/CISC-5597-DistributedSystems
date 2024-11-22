from xmlrpc.server import SimpleXMLRPCServer
import os
import logging
from termcolor import colored  # For colored logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_account(file_name):
    with open(file_name, 'r') as file:
        return float(file.read().strip())

def write_account(file_name, value):
    logging.info(colored(f"writing {file_name}, {value}", 'green'))
    with open(file_name, 'w') as file:
        file.write(f"{value:.2f}")

class ParticipantA:
    def __init__(self):
        self.account_file = "account_A.txt"
        self.temp_file = self.account_file + ".tmp"
        self.prepared = False
        self.transcation_number = None
        self.balance = None
        self.commit_status = False

        with open(self.account_file, "w") as file_A:
            file_A.write(str('200'))

    def canCommit(self, transaction_number):
        self.transcation_number = transaction_number
        try:
            if not os.path.exists(self.account_file):
                self.prepared = False   
                logging.info(colored(f"Account A does not exists", 'red'))
                return self.prepared
            else:
                self.balance = read_account(self.account_file)
                if self.transcation_number == 1:                                    
                    # Simulate the operation: subtract $100 and add 20% bonus
                    if self.balance >= 100:
                        logging.info(colored(f"Account A exists and balance {self.balance} > 100", 'green'))                
                        self.prepared = True
                    else:    
                        logging.info(colored(f"Account A exists and balance {self.balance} < 100", 'red'))
                    return self.prepared   
                elif self.transcation_number == 2:
                    if self.balance > 0:
                        logging.info(colored(f"Account A exists and balance {self.balance} > 0", 'green'))                
                        self.prepared = True
                    else:    
                        logging.info(colored(f"Account A exists and balance {self.balance} <=0", 'red'))
                    return self.prepared      
                else:     
                    logging.info(colored(f"Account A exists but the transaction id is not valid", 'red'))
                    return False
                
        except Exception as e:
            logging.error(colored(f"Error during canCommit for: {str(e)}", 'red'))     
        
    
    def doCommit(self, transaction_number):
        self.transcation_number = transaction_number
        increment = None
        try:
            if self.transcation_number == 1:
                new_balance = self.balance - 100
                write_account(self.account_file, new_balance)
                logging.info(colored(f"Account A updated value from {self.balance} to {new_balance} after Transaction {self.transcation_number}", 'green'))

                self.balance = new_balance
                self.commit_status = True
        

            elif self.transcation_number == 2:
                increment = 0.2 * self.balance
                new_balance = self.balance + increment
                write_account(self.account_file, new_balance)
                self.balance = new_balance
                self.commit_status = True
                logging.info(colored(f"Account A increment value bt {increment} after Transaction {self.transcation_number}", 'green'))
                logging.info(colored(f"Account A new balance: {self.balance}", 'green'))
            
            else:
                logging.info(colored(f"Invlaid transaction {transaction_number} ", 'red'))
            return self.commit_status, increment
        
        except Exception as e:
            logging.error(colored(f"Error during commit: {str(e)}", 'red'))  

    # def prepare(self):
    #     try:
    #         balance = read_account(self.account_file)
    #         logging.info(colored(f"Account A exists", 'green'))
    #         # Simulate the operation: subtract $100 and add 20% bonus
    #         if balance >= 100:
    #             new_balance = balance - 100 + 0.2 * balance
    #             logging.info(colored(f"writing {new_balance}", 'green'))
    #             write_account(self.temp_file, new_balance)
    #             self.prepared = True
    #             return "PREPARED"
    #         else:
    #             return "INSUFFICIENT FUNDS"
    #     except Exception as e:
    #         return f"ERROR: {str(e)}"

    # def commit(self):
    #     if self.prepared and os.path.exists(self.temp_file):
    #         os.replace(self.temp_file, self.account_file)
    #         self.prepared = False
    #         return "COMMITTED"
    #     return "NOT PREPARED"

    def abort(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        self.prepared = False
        return "ABORTED"

def main():
    participant = ParticipantA()
    with SimpleXMLRPCServer(("localhost", 8002),allow_none=True) as server:
        server.register_instance(participant)
        print("Participant A ready on port 8002...")
        logging.info(colored(f"Participant Server started at http://localhost:8002", 'green'))

        server.serve_forever()

if __name__ == "__main__":
    main()
