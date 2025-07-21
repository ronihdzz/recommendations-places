from enum import IntEnum
from typing import Protocol, runtime_checkable


@runtime_checkable          
class InternalCode(Protocol):
    value: int                  
    description: str        

    def to_dict(self) -> dict[str, any]: ...
    

class InternalCodeBase(IntEnum):
    def __new__(cls, value: int, description: str):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._description = description
        return obj

    @property
    def description(self) -> str: 
        return self._description

    def to_dict(self) -> dict:
        return {"code": int(self), "description": self.description}


class CommonInternalCode(InternalCodeBase):
    UNKNOWN                       = 100,  "Unknown error"
    PYDANTIC_VALIDATIONS_REQUEST  = 8001, "Failed Pydantic validations on request"
