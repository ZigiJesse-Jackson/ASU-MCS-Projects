import grpc
import banks_pb2
import banks_pb2_grpc

class Branch(banks_pb2_grpc.BranchServiceServicer):

    def __init__(self, id: int, balance: int, branches: list[int]):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # logical clock of branch
        self.clock = 0

    # Creates stubs to communicate with all branches in list of branches
    def createStub(self):
        for id in self.branches:
            # Ports 50,001 to 50,000+n are used for server communication (n being number of servers)
            port = id+50000
            channel = grpc.insecure_channel(f'localhost:{port}')
            stub = banks_pb2_grpc.BranchServiceStub(channel=channel)
            self.stubList.append([id, stub])

    def _createEvent(self, request_id: int, clock_time: int, interface: str, comment: str):
        # creates event log given customer request id, logical clock value, type of interface, and comment
        event = dict()
        event['customer-request-id'] = request_id
        event['logical_clock'] = clock_time
        event['interface'] = interface
        event['comment'] = comment

        self.recvMsg.append(event)

    def _query(self):
        self.clock+=1
        return self.balance
    
    def _withdraw(self, amount: int, request_id: int):
        # creates stubs for communication when stubs haven't yet been initialized
        if(len(self.stubList)==0):
            self.createStub()

        # communicate to all branches to propagate withdraw query at their site
        for tup in self.stubList:
            print(tup[0])
            id = tup[0]
            stub = tup[1]
            # skip propagation to server itself, update locally
            if id!=self.id:
                self.clock+=1
                self._createEvent(request_id, self.clock, "propagate_withdraw", f'event_sent to branch {id}' )
                request = banks_pb2.BranchMessage(id=self.id, request_id=request_id, interface=banks_pb2.Interface.WITHDRAW, clock_time=self.clock, amount=amount)
                response = stub.Propagate(request)
                if(response.result != banks_pb2.Result.SUCCESS): 
                    return False
            else :
                self.balance-=amount
        return True
    
    def _deposit(self, amount: int, request_id: int):
        # creates stubs for communication when stubs haven't yet been initialized
        if(len(self.stubList)==0):
            self.createStub()

        # communicate to all branches to propagate withdraw query at their site
        for tup in self.stubList:
            id = tup[0]
            stub = tup[1]
            # skip propagation to server itself, update locally
            if id!=self.id:
                self.clock+=1
                self._createEvent(request_id, self.clock, "propagate_deposit", f'event_sent to branch {id}' )
                request = banks_pb2.BranchMessage(id=self.id, request_id=request_id, interface=banks_pb2.Interface.DEPOSIT, clock_time=self.clock, amount=amount)
                response = stub.Propagate(request)
                if(response.result != banks_pb2.Result.SUCCESS): 
                    return False
            else :
                self.balance+=amount
        return True

    def Query(self, request, context):
        self.clock = max(self.clock, request.clock_time)+1
        
        match request.interface:
            case banks_pb2.Interface.QUERY:
                # capture event
                self._createEvent(request.request_id, self.clock, "query", f'event_recv from customer {request.id}' )
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS, balance=self._query())

            case banks_pb2.Interface.WITHDRAW:
                # capture event
                self._createEvent(request.request_id, self.clock, "withdraw", f'event_recv from customer {request.id}' )
                if(self._withdraw(request.amount, request.request_id)):
                    return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)

            case banks_pb2.Interface.DEPOSIT:
                # capture event
                self._createEvent(request.request_id, self.clock, "deposit", f'event_recv from customer {request.id}' )
                if(self._deposit(request.amount, request.request_id)):
                    return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)
            # invalid interface provided
            case _:
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)
   
    def Propagate(self, request, context):
        # propagates withdraw/deposit queries to current branch 
        self.clock = max(self.clock, request.clock_time)+1
        if(request.interface == banks_pb2.Interface.WITHDRAW):
            # capture event 
            self._createEvent(request_id=request.request_id, clock_time=self.clock, interface="propagate_withdraw", comment=f'event_recv from branch {request.id}')
            self.balance-=request.amount
            return banks_pb2.Reply(interface=request.interface, clock_time=self.clock, result=banks_pb2.Result.SUCCESS)
        elif(request.interface == banks_pb2.Interface.DEPOSIT): 
            # capture event
            self._createEvent(request_id=request.request_id, clock_time=self.clock, interface="propagate_deposit", comment=f'event_recv from branch {request.id}')
            self.balance+=request.amount
            return banks_pb2.Reply(interface=request.interface, clock_time=self.clock, result=banks_pb2.Result.SUCCESS)
        return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)
    
    def GetEventsAtBranch(self, request, context):
        # Return all events that occurred at branch
        events = []
        for msg in self.recvMsg:
            event = banks_pb2.BranchEvent(request_id=msg['customer-request-id'],
                                          clock_time=msg['logical_clock'],
                                          interface=msg['interface'],
                                          comment=msg['comment'])
            events.append(event)
        all_events =  banks_pb2.AllBranchEvents()
        all_events.events.extend(events)
        return all_events
