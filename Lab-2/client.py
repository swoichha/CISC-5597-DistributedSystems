import xmlrpc.client
import logging
from termcolor import colored  # For colored logging

# Configure logging for the client
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # List of available server ports
    ports = [8000, 8001, 8002]

    while True:
        # User command input
        command = input("Enter command (e.g., 'set value 5 on 8000' or 'exit' to quit): ").strip()
        
        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break

        if command.startswith("set value"):
            try:
                # Parse value and port from the command
                parts = command.split()
                value = int(parts[2])
                port = int(parts[4])

                # Validate if the port is in available ports
                if port not in ports:
                    logging.error(colored(f"Invalid port {port}. Choose from {ports}.",'red'))
                    continue

                # Connect to the chosen server
                server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")

                # Call the propose_value function on the specified server
                response = server.propose_value(value)
                logging.info(colored(f"Server on port {port} responded: {response}",'green'))

            except (ValueError, IndexError):
                logging.error(colored("Invalid command format. Use 'set value <number> on <port>'.",'red'))
            except Exception as e:
                logging.error(colored(f"Error executing command on server: {e}","red"))
        else:
            logging.error(colored("Invalid command. Use 'set value <number> on <port>' or 'exit' to quit.",'red'))

if __name__ == "__main__":
    main()
