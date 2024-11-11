import xmlrpc.client
import logging
from termcolor import colored
import time
import threading
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from concurrent.futures import ThreadPoolExecutor
def send_propose(server_url, value, node_id, ports,delay):
    """Sends a propose request to the server and returns the response."""
    try:
        server = xmlrpc.client.ServerProxy(server_url,allow_none=True)
        response = server.propose_B(value, node_id, ports,delay)
        logging.info(colored(f"Node {node_id} responded: {response}", 'green'))
    except Exception as e:
        logging.error(colored(f"Error in B_wins_B command: {e}", 'red'))
        response = None
    return response

def restart_all_nodes(ports):
    """Sends a restart command to all nodes to reset their state."""
    for port in ports:
        try:
            server = xmlrpc.client.ServerProxy(f"http://localhost:{port}", allow_none=True)
            server.restart()
            logging.info(colored(f"Node on port {port} has been restarted.", 'green'))
        except Exception as e:
            logging.error(colored(f"Error restarting node on port {port}: {e}", 'red'))


def main():
    ports = [8000,8001,8002,8003,8004]

    while True:
        command = input("Enter command (e.g., 'set value <value> on <node_number>' or 'A_wins <node1_ID> <node2_ID> <valueA><valueB>'): ").strip()

        if command.lower() == "exit":
            logging.info(colored("Exiting client.", 'green'))
            break
        elif command.lower() == "restart":
            restart_all_nodes(ports)

        elif command.startswith("A_wins"):
            try:
                parts = command.split()
                node1_id = int(parts[1])
                node2_id = int(parts[2])
                valueA = int(parts[3])
                valueB = int(parts[4])

                if node1_id not in ports or node2_id not in ports:
                    logging.error(colored("Invalid node IDs.", 'red'))
                    continue
                server1 = xmlrpc.client.ServerProxy(f"http://localhost:{node1_id}",allow_none=True)
                response1 = server1.propose_A(valueA,node1_id,ports[1:3])
                logging.info(colored(f"Node {node1_id} responded: {response1}", 'green'))

                time.sleep(0.01) # delay for 10 milliseconds
                server2 = xmlrpc.client.ServerProxy(f"http://localhost:{node2_id}",allow_none=True)
                response2 = server2.propose_A(valueB,node2_id,ports[2:4])
                logging.info(colored(f"Node {node2_id} responded: {response2}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error in A_wins command: {e}", 'red'))


        elif command.startswith("B_wins") or command.startswith("BB_wins") :
                if command.startswith("B_wins"):
                    delay_arr = [1,0]
                elif command.startswith("BB_wins"):
                    delay_arr = [1,1]
                
                parts = command.split()
                node1_id = int(parts[1])
                node2_id = int(parts[2])
                valueA = int(parts[3])
                valueB = int(parts[4])
                server1_url = f"http://localhost:{node1_id}"
                server2_url = f"http://localhost:{node2_id}"
                if node1_id not in ports or node2_id not in ports:
                    logging.error(colored("Invalid node IDs.", 'red'))
                    continue
                with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit tasks to the executor
                    future1 = executor.submit(send_propose, server1_url, valueA, node1_id, ports[1:3],delay_arr)
                    # Introduce a 10ms delay before the second submission
                    time.sleep(0.1)
                    future2 = executor.submit(send_propose, server2_url, valueB, node2_id, ports[2:4],[0,0])
                # Collect the responses
                response1 = future1.result()
                response2 = future2.result()

                logging.info(colored(f"Final response from Node {node1_id}: {response1}", 'blue'))
                logging.info(colored(f"Final response from Node {node2_id}: {response2}", 'blue'))

                # server1 = xmlrpc.client.ServerProxy(f"http://localhost:{node1_id}")
                # response1 = server1.propose_B(valueA,node1_id,ports[1:3],[1,0])
                # logging.info(colored(f"Node {node1_id} responded: {response1}", 'green'))
                # time.sleep(0.01) # delay for 10 milliseconds
                # server2 = xmlrpc.client.ServerProxy(f"http://localhost:{node2_id}")
                # response2 = server2.propose_B(valueB,node2_id,ports[2:4],[0,0])
                # logging.info(colored(f"Node {node2_id} responded: {response2}", 'green'))

        elif command.startswith("set value"):
            try:
                parts = command.split()
                value = int(parts[2])
                port = int(parts[4])

                if port not in ports:
                    logging.error(colored(f"Invalid port {port}. Choose from {ports}.", 'red'))
                    continue
                other_ports = [p for p in ports if p != port]

                server = xmlrpc.client.ServerProxy(f"http://localhost:{port}")
                response = server.propose_value(value,other_ports)
                logging.info(colored(f"Server on port {port} responded: {response}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error executing command on server: {e}", "red"))
        
        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()