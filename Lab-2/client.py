import xmlrpc.client
import random
import logging

# Configure logging for the client
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # List of available server ports
    ports = [8000, 8001, 8002]
    
    # Randomly select one of the servers for the call
    port = random.choice(ports)
    server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")

    try:
        # Make the RPC calls
        number = 4
        square_result = server.square(number)
        cube_result = server.cube(number)

        # Log the results
        logging.info(f"Server on port {port} handled the operation.")
        logging.info(f"Square of {number}: {square_result}")
        logging.info(f"Cube of {number}: {cube_result}")

    except Exception as e:
        logging.error(f"Error connecting to server on port {port}: {e}")

if __name__ == "__main__":
    main()
