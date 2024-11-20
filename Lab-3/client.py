from xmlrpc.client import ServerProxy
import logging
from termcolor import colored


def main():
    coordinator = ServerProxy("http://localhost:8001")

    while True:
        command = input("Enter command (e.g., 'scenario 1' or 'scenario 2'): ").strip()

        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break

        elif command.startswith("scenario 1") or command.startswith("scenario 2") or command.startswith("scenario 3") or command.startswith("scenario 4"):
            try:
                parts = command.split()
                initial_balance_A = int(parts[1])
                initial_balance_B = int(parts[2])
                crash_node = int(parts[3])              

                
                result = coordinator.simulate_scenario(initial_balance_A, initial_balance_B, crash_node)                
                logging.info(colored(f"{result}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error in A_wins command: {e}", 'red'))
        
        elif command.startswith("restart"):
            coordinator.restart()

        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()