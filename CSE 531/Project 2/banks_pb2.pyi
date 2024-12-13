from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

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
    __slots__ = ("id", "clock_time", "request_id", "interface", "amount")
    ID_FIELD_NUMBER: _ClassVar[int]
    CLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    id: int
    clock_time: int
    request_id: int
    interface: Interface
    amount: int
    def __init__(self, id: _Optional[int] = ..., clock_time: _Optional[int] = ..., request_id: _Optional[int] = ..., interface: _Optional[_Union[Interface, str]] = ..., amount: _Optional[int] = ...) -> None: ...

class BranchMessage(_message.Message):
    __slots__ = ("id", "request_id", "interface", "amount", "clock_time")
    ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    id: int
    request_id: int
    interface: Interface
    amount: int
    clock_time: int
    def __init__(self, id: _Optional[int] = ..., request_id: _Optional[int] = ..., interface: _Optional[_Union[Interface, str]] = ..., amount: _Optional[int] = ..., clock_time: _Optional[int] = ...) -> None: ...

class BranchEvent(_message.Message):
    __slots__ = ("request_id", "clock_time", "interface", "comment")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    CLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    request_id: int
    clock_time: int
    interface: str
    comment: str
    def __init__(self, request_id: _Optional[int] = ..., clock_time: _Optional[int] = ..., interface: _Optional[str] = ..., comment: _Optional[str] = ...) -> None: ...

class AllBranchEvents(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[BranchEvent]
    def __init__(self, events: _Optional[_Iterable[_Union[BranchEvent, _Mapping]]] = ...) -> None: ...

class RequestEvents(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class Reply(_message.Message):
    __slots__ = ("interface", "result", "clock_time", "balance")
    INTERFACE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    CLOCK_TIME_FIELD_NUMBER: _ClassVar[int]
    BALANCE_FIELD_NUMBER: _ClassVar[int]
    interface: Interface
    result: Result
    clock_time: int
    balance: int
    def __init__(self, interface: _Optional[_Union[Interface, str]] = ..., result: _Optional[_Union[Result, str]] = ..., clock_time: _Optional[int] = ..., balance: _Optional[int] = ...) -> None: ...
