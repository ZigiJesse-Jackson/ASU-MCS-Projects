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

    # TODO: students are expected to create the Customer stub
    def createStub(self):
        # Ports 50,001 to 50,000+n are used for server communication (n being number of servers)
        port = self.id+50000
        channel = grpc.insecure_channel(f'localhost:{port}')
        self.stub = banks_pb2_grpc.BranchServiceStub(channel)

    # TODO: students are expected to send out the events to the Bank
    def executeEvents(self):
        # instantiate stub for communication with server
        self.createStub()
        for event in self.events:
            processed_event = dict()
            interface = None

            match event['interface']:
                case "query":
                    interface = banks_pb2.Interface.QUERY
                    request = banks_pb2.CustomerMessage(id=self.id, interface=interface)

                case "withdraw":
                    interface = banks_pb2.Interface.WITHDRAW
                    request = banks_pb2.CustomerMessage(id=self.id, interface=interface, amount=event['money'])

                case "deposit": 
                    interface = banks_pb2.Interface.DEPOSIT
                    request = banks_pb2.CustomerMessage(id=self.id, interface=interface, amount=event['money'])

            response = self.stub.Query(request)
            processed_event['interface'] = event['interface']
            # balance field is only instantiated when interface is query
            # result field is only instantiated when interface is not query
            if(event['interface'] == "query"): 
                processed_event['balance'] = response.balance
            elif(response.result == banks_pb2.Result.SUCCESS):
                processed_event['result'] = "success"
            else: processed_event['result'] = "failure"

            self.recvMsg.append(processed_event)
        self.stub = None

    def returnMsgs(self):
        return self.recvMsg


