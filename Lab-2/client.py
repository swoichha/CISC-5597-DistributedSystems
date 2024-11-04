import xmlrpc.client
import random
import logging

# Configure logging for the client
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # List of available server ports
    ports = [8000, 8001, 8002]
    
    while True:
        # User command input
        command = input("Enter command (e.g., 'set value 5' or 'exit' to quit): ").strip()
        
        if command.lower() == "exit":
            logging.info("Exiting client.")
            break
        
        if command.startswith("set value"):
            try:
                # Parse value from the command
                value = int(command.split()[2])
                
                # Randomly select one of the servers for the call
                port = random.choice(ports)
                server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")

                # Call the set_value function on the server
                response = server.set_value(value)
                logging.info(f"Server on port {port} responded: {response}")

            except ValueError:
                logging.error("Invalid command format. Use 'set value <number>'.")
            except Exception as e:
                logging.error(f"Error executing command on server: {e}")
        else:
            logging.error("Invalid command. Use 'set value <number>' or 'exit' to quit.")

if __name__ == "__main__":
    main()
