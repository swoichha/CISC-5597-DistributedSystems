import xmlrpc.client
import logging
from termcolor import colored
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define IP addresses for each port
server_ips = {
    8000: "10.128.0.10",
    8001: "10.128.0.6",
    8002: "10.128.0.7",
    8003: "10.128.0.5",
    8004: "10.128.0.9"
}
    
def get_server_url(port):
    """Returns the server URL based on the port."""
    ip = server_ips.get(port, "localhost")
    url = f"http://{ip}:{port}"
    return url
     
def send_propose(server_url, value, node_id, ports, delay):
    """Sends a propose request to the server and returns the response."""
    try:
        server = xmlrpc.client.ServerProxy(server_url, allow_none=True)
        response = server.propose_B(value, node_id, ports, delay)
        logging.info(colored(f"Node {node_id} responded: {response}", 'green'))
    except Exception as e:
        logging.error(colored(f"Error in B_wins_B command: {e}", 'red'))
        response = None
    return response

def send_propose_cont(server_url, value,node_id, proposal_num, ports,delay):
    """Sends a propose request to the server and returns the response."""
    try:
        server = xmlrpc.client.ServerProxy(server_url,allow_none=True)
        response = server.propose_livelock(value, proposal_num, node_id, ports,delay)
        logging.info(colored(f"Node {node_id} responded: {response}", 'green'))
        return response
    except Exception as e:
        logging.error(colored(f"Error in livelock command: {e}", 'red'))
        return False
    
def restart_all_nodes(ports):
    """Sends a restart command to all nodes to reset their state."""
    for port in ports:
        try:
            server_url = get_server_url(port)
            server = xmlrpc.client.ServerProxy(server_url, allow_none=True)
            server.restart()
            logging.info(colored(f"Node on port {port} has been restarted.", 'green'))
        except Exception as e:
            logging.error(colored(f"Error restarting node on port {port}: {e}", 'red'))

def main():
    ports = [8000, 8001, 8002, 8003, 8004]

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

                server1_url = get_server_url(node1_id)
                server2_url = get_server_url(node2_id)

                server1 = xmlrpc.client.ServerProxy(server1_url, allow_none=True)
                response1 = server1.propose_A(valueA, node1_id, ports[1:3])
                logging.info(colored(f"Node {node1_id} responded: {response1}", 'green'))

                time.sleep(0.01)  # delay for 10 milliseconds
                server2 = xmlrpc.client.ServerProxy(server2_url, allow_none=True)
                response2 = server2.propose_A(valueB, node2_id, ports[2:4])
                logging.info(colored(f"Node {node2_id} responded: {response2}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error in A_wins command: {e}", 'red'))


        elif command.startswith("B_wins") or command.startswith("BB_wins"):
            delay_arr = [1, 0] if command.startswith("B_wins") else [1, 1]
            parts = command.split()
            node1_id = int(parts[1])
            node2_id = int(parts[2])
            valueA = int(parts[3])
            valueB = int(parts[4])

            server1_url = get_server_url(node1_id)
            server2_url = get_server_url(node2_id)

            if node1_id not in ports or node2_id not in ports:
                logging.error(colored("Invalid node IDs.", 'red'))
                continue

            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(send_propose, server1_url, valueA, node1_id, ports[1:3], delay_arr)
                time.sleep(0.1)  # 100ms delay before the second submission
                future2 = executor.submit(send_propose, server2_url, valueB, node2_id, ports[2:4], [0, 0])

            response1 = future1.result()
            response2 = future2.result()

            logging.info(colored(f"Final response from Node {node1_id}: {response1}", 'blue'))
            logging.info(colored(f"Final response from Node {node2_id}: {response2}", 'blue'))


        elif command.startswith("set value"):
            try:
                parts = command.split()
                value = int(parts[2])
                port = int(parts[4])

                if port not in ports:
                    logging.error(colored(f"Invalid port {port}. Choose from {ports}.", 'red'))
                    continue

                server_url = get_server_url(port)
                other_ports = [p for p in ports if p != port]

                server = xmlrpc.client.ServerProxy(server_url)
                response = server.propose_value(value, other_ports)
                logging.info(colored(f"Server on port {port} responded: {response}", 'green'))

            except Exception as e:
                logging.error(colored(f"Error executing command on server: {e}", "red"))

        elif command.startswith("livelock"): # livelock <node1> <node2> <val1> <val2>
            try:
                delay_arr=[1,1]
                parts = command.split()
                node1_id = int(parts[1])
                node2_id = int(parts[2])
                valueA = int(parts[3])
                valueB = int(parts[4])

                server1_url = get_server_url(node1_id)
                server2_url = get_server_url(node2_id)

                if node1_id not in ports or node2_id not in ports:
                    logging.error(colored("Invalid node IDs.", 'red'))
                    continue

                max_retries = 9
                retry_count1 = 0
                retry_count2 = 0
                proposal_num2 = node2_id
                proposal_num1 = node1_id

                while retry_count1 < max_retries and retry_count2 < max_retries:
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future1 = executor.submit(send_propose_cont, server1_url, valueA, node1_id,node1_id, ports[1:3],delay_arr)
                        time.sleep(0.1)
                        future2 = executor.submit(send_propose_cont, server2_url, valueB, node2_id, node2_id,ports[2:4],delay_arr)
                        while not future1.done() or not future2.done():

                            if future1.done():
                                response1 = future1.result()
                                if response1 == False:
                                    retry_count1 +=1
                                    proposal_num1 = proposal_num1 + 1
                                    logging.warning(colored(f"Retrying {retry_count1} of {max_retries} for port {node1_id} with proposal number {proposal_num1}","yellow"))
                                    if retry_count1 >= max_retries:
                                        logging.warning(colored(f"Node {node1_id} failed after retries, retrying with new proposal.", 'red'))
                                        break
                                    future1 = executor.submit(send_propose_cont, server1_url, valueA, node1_id,proposal_num1,  ports[1:3], delay_arr)

                            if future2.done():
                                response2 = future2.result()
                                if response2 == False:
                                    proposal_num2 =proposal_num2 + 1
                                    retry_count2+=1
                                    logging.warning(colored(f"Retrying {retry_count2} of {max_retries} for port {node2_id} with {proposal_num2}","yellow"))
                                    if retry_count2 >=max_retries:
                                        logging.warning(colored(f"Node {node2_id} failed after retries, retrying with new proposal.", 'red'))
                                        break
                                    # Increment proposal for node2 and submit again
                                    
                                    future2 = executor.submit(send_propose_cont,server2_url,valueB, node2_id, proposal_num2, ports[2:4], delay_arr)

                            time.sleep(0.1)  # Sleep for a small interval to check the task completion


                # Collect the responses
                response1 = future1.result()
                response2 = future2.result()

                logging.info(colored(f"Final response from Node {node1_id}: {response1}", 'blue'))
                logging.info(colored(f"Final response from Node {node2_id}: {response2}", 'blue'))

            except Exception as e:
                logging.error(colored(f"Error executing command on server: {e}", "red"))

        else:
            logging.error(colored("Invalid command.", 'red'))

if __name__ == "__main__":
    main()