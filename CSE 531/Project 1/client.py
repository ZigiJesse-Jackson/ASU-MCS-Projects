from customer import Customer
import json
import sys


def read_json_grpc_client(file_name):
    """Reads input json file for gRPC project and outputs a list of Customer objects

    Args:
        file_name (str): file to read in input for Customer objects creation
    
    Returns:
        list (Customer): a list of Customer objects that that can communicate with a Branch server according to their id 
    
    """
    json_file = open(file_name)
    data = json.load(json_file)
    customers = []
    for record in data:
        if( record['type'] == "customer"): 
            curr_customer = Customer(record['id'], record['events'])
            customers.append(curr_customer)
    json_file.close()
    return customers

def run_clients(file_name):
    """Executes Customer events

    Args:
        file_name (str): file to read in input for Customer objects creation
    
    Returns:
        events_processed (list): A dictionary of id and events processed linked to id
    """
    events_processed = []
    customers = read_json_grpc_client(file_name)
    for customer in customers:
        event_processed = dict()
        event_processed['id'] = customer.id
        customer.executeEvents()
        event_processed['recv'] = customer.returnMsgs()
        events_processed.append(event_processed)
    return events_processed
   
    



if __name__ == '__main__':
    file = sys.argv[1]
    
    events_processed = run_clients(file)
    with open("output.json", "w") as output_file:
        json.dump(events_processed, output_file)
    output_file.close()