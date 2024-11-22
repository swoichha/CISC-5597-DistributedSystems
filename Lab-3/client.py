from xmlrpc.client import ServerProxy
import logging
from termcolor import colored

import logging
from termcolor import colored  # For colored logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def main():
    coordinator = ServerProxy("http://localhost:8001", allow_none=True)

    while True:
        command = input("Enter command (e.g., 'scenario1' or 'scenario2'): ").strip()

        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break

        elif command.startswith("scenario1"):
            try:
                parts = command.split()
                first_transaction_number = int(parts[1])
                second_transaction_number = int(parts[2])
                print("/*/*/*/**/", first_transaction_number, second_transaction_number)
                
                resultMsg1, transaction1_status = coordinator.execute_transaction(first_transaction_number)   
                print("*/*/****/**/*/**",resultMsg1, transaction1_status)
                if transaction1_status:
                    logging.info(colored(f"{resultMsg1}", 'green'))
                else:
                    logging.info(colored(f"{resultMsg1}", 'red'))   

                resultMsg2, transaction2_status = coordinator.execute_transaction(second_transaction_number)   
                if transaction2_status:
                    logging.info(colored(f"{resultMsg2}", 'green'))
                else:
                    logging.info(colored(f"{resultMsg2}", 'red'))   

            except Exception as e:
                logging.error(colored(f"Error in command: {e}", 'red'))
        
        elif command.startswith("restart"):
            coordinator.restart()

        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()