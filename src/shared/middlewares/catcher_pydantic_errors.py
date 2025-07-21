from collections import defaultdict

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from shared.base_internal_codes import CommonInternalCode

from shared.base_responses import create_response_for_fast_api


def CatcherExceptionsPydantic(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validate(_: Request, exc: Exception):
        error_detail = defaultdict(list)
        for error in exc.errors():
            field = error["loc"][1] if "loc" in error else None
            error_msg = error["msg"]
            error_detail[field].append(error_msg)

        return create_response_for_fast_api(
            data=error_detail,
            status_code_http=status.HTTP_400_BAD_REQUEST,
            error_code=CommonInternalCode.PYDANTIC_VALIDATIONS_REQUEST
        )