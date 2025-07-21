from typing import TypeVar, Any
from pydantic import BaseModel
from shared.base_contextvars import ctx_trace_id
from fastapi.responses import JSONResponse
import fastapi
import json
from shared.base_internal_codes import InternalCode
from shared.base_internal_codes import CommonInternalCode as CC

T = TypeVar("T", bound=InternalCode)

class EnvelopeResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | list |  None = None
    trace_id: str | None = None

class ErrorDetailResponse(BaseModel):
    internal_error: dict[str, Any]
    details: dict[str, Any]

    @staticmethod
    def from_error_code(error_code: T | None = CC.UNKNOWN, details: dict[str, Any] | None = None) -> 'ErrorDetailResponse':
        return ErrorDetailResponse(
            internal_error={
                "code": error_code.value,
                "description": error_code.description,
            },
            details=details or {}
        ).model_dump()

def create_response_for_fast_api(
    status_code_http: int = fastapi.status.HTTP_200_OK,
    data: Any = None,
    error_code: T | None = CC.UNKNOWN,
    message: str | None = None
) -> JSONResponse:
    success = 200 <= status_code_http < 300
    message = message or ("Operation successful" if success else "An error occurred")

    if isinstance(data,list):
        if len(data) == 0:
            data = None
        else:
            first_element = data[0]
            if isinstance(first_element,BaseModel):
                data = [element.model_dump(mode="json") for element in data]
                

    elif isinstance(data, BaseModel):
        data = data.model_dump_json()
        data = json.loads(data)

    if not success:
        data = ErrorDetailResponse.from_error_code(error_code=error_code, details=data)

    envelope_response = EnvelopeResponse(
        success=success,
        message=message,
        data=data,
        trace_id=ctx_trace_id.get()
    )
    
    return JSONResponse(
        content=envelope_response.model_dump(),
        status_code=status_code_http
    )