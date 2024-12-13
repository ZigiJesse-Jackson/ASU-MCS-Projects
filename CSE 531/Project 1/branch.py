import grpc
import banks_pb2
import banks_pb2_grpc

class Branch(banks_pb2_grpc.BranchServiceServicer):

    def __init__(self, id, balance, branches):
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
        # iterate the processID of the branches

        # TODO: students are expected to store the processID of the branches
        pass

    # TODO: students are expected to process requests from both Client and Branch
    def MsgDelivery(self,request, context):
        pass
    
    # Creates stubs to communicate with all branches in list of branches
    def createStub(self):
        for id in self.branches:
            # Ports 50,001 to 50,000+n are used for server communication (n being number of servers)
            port = id+50000
            channel = grpc.insecure_channel(f'localhost:{port}')
            stub = banks_pb2_grpc.BranchServiceStub(channel=channel)
            self.stubList.append(stub)


    def _query(self):
        return self.balance
    
    def _withdraw(self, amount):
        # creates stubs for communication when stubs haven't yet been initialized
        if(len(self.stubList)==0):
            self.createStub()

        # communicate to all branches to propogate withdraw query at their site
        for stub in self.stubList:
            request = banks_pb2.BranchMessage(interface=banks_pb2.Interface.WITHDRAW, amount=amount)
            response = stub.Propagate(request)
            if(response.result != banks_pb2.Result.SUCCESS): return False
        return True
    
    def _deposit(self, amount):
        # creates stubs for communication when stubs haven't yet been initialized
        if(len(self.stubList)==0):
            self.createStub()

        # communicate to all branches to propogate withdraw query at their site
        for stub in self.stubList:
            request = banks_pb2.BranchMessage(interface=banks_pb2.Interface.DEPOSIT, amount=amount)
            response = stub.Propagate(request)
            if(response.result != banks_pb2.Result.SUCCESS): return False
        return True

    def Query(self, request, context):
        match request.interface:
            case banks_pb2.Interface.QUERY:
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS, balance=self._query())

            case banks_pb2.Interface.WITHDRAW:
                if(self._withdraw(request.amount)):
                    return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)

            case banks_pb2.Interface.DEPOSIT:
                if(self._deposit(request.amount)):
                    return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)
            # invalid interface provided
            case _:
                return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)

    # propogates withdraw/deposit queries to current branch    
    def Propagate(self, request, context):
        if(request.interface == banks_pb2.Interface.WITHDRAW): 
            self.balance-=request.amount
            return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
        elif(request.interface == banks_pb2.Interface.DEPOSIT): 
            self.balance+=request.amount
            return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.SUCCESS)
        return banks_pb2.Reply(interface=request.interface, result=banks_pb2.Result.FAILURE)
