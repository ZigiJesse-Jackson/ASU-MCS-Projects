from customer import Customer
from multiprocessing import Process, Queue
import json
import sys


def read_json_grpc_client(file_name: str)->list[Customer]:
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
            curr_customer = Customer(record['id'], record['customer-requests'])
            customers.append(curr_customer)
    json_file.close()
    return customers

def execute_events_in_Customer(customer: Customer, queue: Queue):
    """Executes "executeEvents()" Customer method then places it in multiprocessing Queue
    Args:
        customer (Customer): Customer object 
        queue (Queue): multiprocessing library Queue
    
    """
    customer.executeEvents()
    queue.put(customer)

def get_all_customers_branch_events(customers: list[Customer])->list[dict]:
    """Retrieves events at a Customer's branch for all Customer objects
    Args:
        customers (list[Customer]): list of Customer objects
    Returns:
        list[dict]: a list of branch events at each Customer object's branch
    """
    all_branch_events = []
    for i in range(len(customers)):
        customer = customers[i]
        all_branch_events.append(customer.requestEventsAtBranch())
    return all_branch_events


def run_clients(file_name: str)->list[dict]:
    """Runs Customer clients by reading in Customer details in json file and creating Customer objects, executing events at Customer, then retrieving all events associated with the Customer events executed 

    Args:
        file_name (str): file to read in input for Customer objects creation
    
    Returns:
        list[dict]: list of all events, in the order of Customer events, Branch events, and all events
    """
    all_customer_events = []
    processes = []
    customers = read_json_grpc_client(file_name)
    # queue to pass computed customer object for retrieval of customer events that happened in process
    queue = Queue()
    for i in range(len(customers)):
        customer_events = dict()
        customer_events['id'] = customers[i].id
        customer_events['type'] = "customer"

        # spin up a separate process for each customer
        p = Process(target=execute_events_in_Customer, args=(customers[i], queue))
        processes.append(p)
        p.start()
        all_customer_events.append(customer_events)
    
    for p in processes:
        p.join()
    
    customers.clear()
    # recapture customers executed in simultaneously run processes
    while(queue.empty()==False):
        customers.append(queue.get())

    # capture events from customers
    for i in range(len(customers)):
        all_customer_events[i]['events'] = customers[i].returnMsgs()
    
    # capture all events at branches
    all_customer_branch_events = get_all_customers_branch_events(customers)

    all_events = all_customer_events+all_customer_branch_events
    events_in_entities = []

    # capture all events across both customer and branch
    for entity in all_events:
        for event in entity['events']:
            reformed_event = dict()
            reformed_event['id'] = entity['id']
            reformed_event['customer-request-id'] = event['customer-request-id']
            reformed_event['type'] = entity['type']
            reformed_event['logical_clock'] = event['logical_clock']
            reformed_event['interface'] = event['interface']
            reformed_event['comment'] = event['comment']
            events_in_entities.append(reformed_event)
            
    return all_customer_events+all_customer_branch_events+events_in_entities
   

if __name__ == '__main__':
    file = sys.argv[1]
    
    all_events = run_clients(file)
    with open("output.json", "w") as output_file:
        json.dump(all_events, output_file)
    output_file.close()