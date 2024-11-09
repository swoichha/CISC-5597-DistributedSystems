import xmlrpc.client
import logging
from termcolor import colored
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    ports = [8000, 8001, 8002]

    while True:
        command = input("Enter command (e.g., 'set value <value> on <node_number>', 'A_wins <nodeA_ID> <nodeB_ID> <valueA> <valueB> <delay>', 'restart'): ").strip()
        
        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break

        if command.startswith("A_wins") or command.startswith("B_wins"):
            try:
                parts = command.split()
                operation = parts[0]
                nodeA_id = int(parts[1])
                nodeB_id = int(parts[2])
                valueA = int(parts[3])
                valueB = int(parts[4])
                delay = int(parts[5]) if len(parts) > 5 else 0  # Optional delay parameter

                if nodeA_id not in ports or nodeB_id not in ports:
                    logging.error(colored("Invalid node IDs. Please choose from available ports.", 'red'))
                    continue

                # Select the correct winner's delay based on the operation
                winning_node_delayed = True if operation == "A_wins" else False

                # Connect and propose value for Node A
                serverA = xmlrpc.client.ServerProxy(f"http://localhost:{nodeA_id}")
                responseA = serverA.propose_value(valueA, winning_node_delayed, delay)
                logging.info(colored(f"Node {nodeA_id} responded: {responseA}", 'green'))

                # Slight delay before proposing to Node B
                time.sleep(0.01)
                serverB = xmlrpc.client.ServerProxy(f"http://localhost:{nodeB_id}")
                responseB = serverB.propose_value(valueB)
                logging.info(colored(f"Node {nodeB_id} responded: {responseB}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error in '{operation}' command: {e}", 'red'))

        elif command.startswith("set value"):
            try:
                parts = command.split()
                value = int(parts[2])
                port = int(parts[4])

                if port not in ports:
                    logging.error(colored(f"Invalid port {port}. Choose from {ports}.", 'red'))
                    continue

                server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")
                response = server.propose_value(value)
                logging.info(colored(f"Server on port {port} responded: {response}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error executing 'set value' command: {e}", "red"))
        
        elif command.lower() == "restart":
            try:
                # Iterate over all ports to restart each server
                for port in ports:
                    server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")
                    response = server.restart_server()
                    logging.info(colored(f"Server on port {port} restarted: {response}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error restarting servers: {e}", "red"))
        
        else:
            logging.error(colored("Invalid command. Please follow the correct syntax.", 'red'))

if __name__ == "__main__":
    main()
