from xmlrpc.client import ServerProxy
import logging
from termcolor import colored
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    coordinator = ServerProxy("http://localhost:8001", allow_none=True)

    while True:
        command = input("Enter command (e.g., 'scenario <scenario_number>: <first_transaction_number> <second_transaction_number>'): ").strip()

        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break
        elif command.startswith("restart"):
            resultMsg, restart_status = coordinator.restart()
            if restart_status:
                logging.info(colored(f"Restart status: {resultMsg}", 'green'))
            else:
                logging.info(colored(f"Restart status: {resultMsg}", 'red'))
        elif command.startswith("scenario"):
            try:
                # Validate and parse the command
                if ':' not in command:
                    raise ValueError("Invalid format. Use 'scenario <scenario_number>: <first_transaction_number> <second_transaction_number>'.")

                scenario_part, transactions_part = command.split(":", 1)
                scenario_number = int(scenario_part.split()[1])
                transaction_numbers = transactions_part.strip().split()

                # Validate scenario number
                if scenario_number < 1 or scenario_number > 4:
                    raise ValueError(f"Invalid scenario number '{scenario_number}'. Allowed values are 1, 2, 3, or 4.")

                # Validate transaction numbers
                if len(transaction_numbers) != 2:
                    raise ValueError("Please provide exactly two transaction numbers.")

                first_transaction_number = int(transaction_numbers[0])
                second_transaction_number = int(transaction_numbers[1])

                if first_transaction_number not in [1, 2] or second_transaction_number not in [1, 2]:
                    raise ValueError(f"Invalid transaction numbers '{first_transaction_number}' or '{second_transaction_number}'. Allowed values are 1 or 2.")

                logging.info(colored(f"Executing Scenario {scenario_number} with transactions {first_transaction_number} and {second_transaction_number}.", 'blue'))

                # Execute the first transaction
                resultMsg1, first_transaction_status = coordinator.execute_transaction(scenario_number, first_transaction_number)
                if first_transaction_status:
                    logging.info(colored(f"Transaction {first_transaction_number} Status: {resultMsg1}", 'green'))
                else:
                    logging.info(colored(f"Transaction {first_transaction_number} Status: {resultMsg1}", 'red'))
                
                # Execute the second transaction
                time.sleep(5)
                resultMsg2, second_transaction_status = coordinator.execute_transaction(scenario_number, second_transaction_number)
                if second_transaction_status:
                    logging.info(colored(f"Transaction {second_transaction_number} Status: {resultMsg2}", 'green'))
                else:
                    logging.info(colored(f"Transaction {second_transaction_number} Status: {resultMsg2}", 'red'))

            except ValueError as ve:
                logging.error(colored(f"Validation error: {ve}", 'red'))
            except Exception as e:
                logging.error(colored(f"Error in command: {e}", 'red'))                

        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()
