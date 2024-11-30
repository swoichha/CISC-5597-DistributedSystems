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
                logging.info(colored(f"Restart status: {resultMsg} ", 'green'))
            else:
                logging.info(colored(f"Restart status: {resultMsg} ", 'red'))
        elif command.startswith("scenario 1") or command.startswith("scenario 2") or command.startswith("scenario 3") or command.startswith("scenario 4"):
            try:
                # Validate and parse the command
                if ':' not in command:
                    raise ValueError("Invalid format. Use 'scenario <scenario_number>: <first_transaction_number> <second_transaction_number>'.")

                scenario_part, transactions_part = command.split(":", 1)
                scenario_number = int(scenario_part.split()[1])
                transaction_numbers = transactions_part.strip().split()

                if len(transaction_numbers) != 2:
                    raise ValueError("Please provide exactly two transaction numbers.")

                first_transaction_number = int(transaction_numbers[0])
                second_transaction_number = int(transaction_numbers[1])

                logging.info(colored(f"Executing Scenario {scenario_number} with transactions {first_transaction_number} and {second_transaction_number}.", 'blue'))

                # Execute the first transaction
                resultMsg1, first_transaction_status = coordinator.execute_transaction(scenario_number, first_transaction_number)
                if first_transaction_status:
                    logging.info(colored(f"Transaction {first_transaction_number} Status: {resultMsg1}", 'green'))
                else:
                    logging.info(colored(f"Transaction {first_transaction_number} Status: {resultMsg1}", 'red'))
                # Execute the second transaction
                resultMsg2, second_transaction_status = coordinator.execute_transaction(scenario_number, second_transaction_number)
                if second_transaction_status:
                    logging.info(colored(f"Transaction {second_transaction_number} Status: {resultMsg2}", 'green'))
                else:
                    logging.info(colored(f"Transaction {second_transaction_number} Status: {resultMsg2}", 'red'))

            except Exception as e:
                logging.error(colored(f"Error in command: {e}", 'red'))        

        elif command.startswith("restart"):
            try:
                coordinator.restart()
                logging.info(colored("Coordinator restarted successfully.", 'green'))
            except Exception as e:
                logging.error(colored(f"Error restarting coordinator: {e}", 'red'))

        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()
