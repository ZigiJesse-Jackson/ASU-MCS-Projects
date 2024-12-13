from multiprocessing import Process
from concurrent import futures
import grpc 
import banks_pb2_grpc
from branch import Branch
import json
import sys

def read_json_grpc_server(file_name):
    """Reads input json file for gRPC project and outputs two lists, a list of dictionaries containing branch setup information
    and a list containing all branch ids

    Args:
        file_name (str): file to read in input for Customer objects creation
    
    Returns:
        tuple (list (dict), list (int)): list of dictionaries containing branch setup information
    and a list containing all branch ids
    """
    json_file = open(file_name)
    data = json.load(json_file)
    server_info = []
    branch_ids = []
    for record in data:
        if( record['type'] =="branch"): 
            branch_ids.append(record['id'])
            server_info.append(record)
    json_file.close()
    return server_info, branch_ids

def serve(port, id, balance, branches):
    """Creates a branch server
    Args: 
        port (int): port to communicate to branch server
        id (int): branch id
        balance (int): initial branch balance
        branches (list (int)): ids of branches the branch server can communicate with

    """
    branch = Branch(id, balance, branches)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banks_pb2_grpc.add_BranchServiceServicer_to_server(branch, server)
    server.add_insecure_port(f'localhost:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    file = sys.argv[1]
    
    server_info, branch_ids = read_json_grpc_server(file)

    processes = []
    # initialize each branch server in a different process
    for info in server_info: 
        # Ports 50,001 to 50,000+n are used for server communication (n being number of servers) 
        port = info['id']+50000
        id = info['id']
        bank_balance = info['balance']

        p = Process(target=serve, args=(port, id, bank_balance, branch_ids))
        processes.append(p)
        p.start()

    for p in processes:
        p.join() 