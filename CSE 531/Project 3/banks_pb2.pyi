from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Interface(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WITHDRAW: _ClassVar[Interface]
    DEPOSIT: _ClassVar[Interface]
    QUERY: _ClassVar[Interface]

class Result(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUCCESS: _ClassVar[Result]
    FAILURE: _ClassVar[Result]
WITHDRAW: Interface
DEPOSIT: Interface
QUERY: Interface
SUCCESS: Result
FAILURE: Result

class CustomerMessage(_message.Message):
    __slots__ = ("id", "request_id", "interface", "amount", "writeset")
    ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    WRITESET_FIELD_NUMBER: _ClassVar[int]
    id: int
    request_id: int
    interface: Interface
    amount: int
    writeset: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., request_id: _Optional[int] = ..., interface: _Optional[_Union[Interface, str]] = ..., amount: _Optional[int] = ..., writeset: _Optional[_Iterable[int]] = ...) -> None: ...

class BranchMessage(_message.Message):
    __slots__ = ("interface", "request_id", "amount", "writeset")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    WRITESET_FIELD_NUMBER: _ClassVar[int]
    interface: Interface
    request_id: int
    amount: int
    writeset: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, interface: _Optional[_Union[Interface, str]] = ..., request_id: _Optional[int] = ..., amount: _Optional[int] = ..., writeset: _Optional[_Iterable[int]] = ...) -> None: ...

class Reply(_message.Message):
    __slots__ = ("interface", "result", "balance")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    BALANCE_FIELD_NUMBER: _ClassVar[int]
    interface: Interface
    result: Result
    balance: int
    def __init__(self, interface: _Optional[_Union[Interface, str]] = ..., result: _Optional[_Union[Result, str]] = ..., balance: _Optional[int] = ...) -> None: ...
