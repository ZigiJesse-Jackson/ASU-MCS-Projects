import grpc
import banks_pb2
import banks_pb2_grpc

class Customer:
    def __init__(self, id, events):
        # unique ID of the Customer
        self.id = id
        # events from the input
        self.events = events
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # pointer for the stub
        self.stub = None
        # logical clock of customer
        self.clock = 0

    # TODO: students are expected to create the Customer stub
    def createStub(self):
        # Ports 50,001 to 50,000+n are used for server communication (n being number of servers)
        port = self.id+50000
        channel = grpc.insecure_channel(f'localhost:{port}')
        self.stub = banks_pb2_grpc.BranchServiceStub(channel)
    
    def _createEvent(self, request_id: int, clock_time: int, interface: str, comment: str):
        # creates event log given customer request id, logical clock value, type of interface, and comment
        event = dict()
        event['customer-request-id'] = request_id
        event['logical_clock'] = clock_time
        event['interface'] = interface
        event['comment'] = comment

        self.recvMsg.append(event)

    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        # instantiate stub for communication with server
        self.createStub()
        for event in self.events:
            self.clock+=1
            processed_event = dict()
            interface = None

            match event['interface']:
                case "query":
                    interface = banks_pb2.Interface.QUERY
                    request = banks_pb2.CustomerMessage(
                        id=self.id, 
                        clock_time=self.clock, 
                        request_id=event['customer-request-id'], 
                        interface=interface)

                case "withdraw":
                    interface = banks_pb2.Interface.WITHDRAW
                    request = banks_pb2.CustomerMessage(
                        id=self.id,
                        clock_time=self.clock, 
                        request_id=event['customer-request-id'], 
                        interface=interface, 
                        amount=event['money'])

                case "deposit": 
                    interface = banks_pb2.Interface.DEPOSIT
                    request = banks_pb2.CustomerMessage(
                        id=self.id, 
                        clock_time=self.clock, 
                        request_id=event['customer-request-id'], 
                        interface=interface, 
                        amount=event['money'])
            self.stub.Query(request)
            # caputre event
            self._createEvent(request_id=event['customer-request-id'], clock_time=self.clock, interface=event['interface'], comment=f'event_sent from customer {self.id}')
            processed_event['interface'] = event['interface']
        self.stub = None
    
    def requestEventsAtBranch(self):
        # requests for all events at customer's branch
        self.createStub()
        message = banks_pb2.RequestEvents()
        response_list = self.stub.GetEventsAtBranch(message)
        all_branch_events = dict()
        all_branch_events['id'] = self.id
        all_branch_events['type'] = "branch"
        all_branch_events['events'] = []
        for response in response_list.events:
            event = dict()
            event['customer-request-id'] = response.request_id
            event['logical_clock'] = response.clock_time
            event['interface'] = response.interface
            event['comment'] = response.comment
            all_branch_events['events'].append(event)
        self.stub = None
        return all_branch_events


    
    def returnMsgs(self):
        return self.recvMsg


