from shared.base_exceptions import BaseApiRestException
from core.internal_codes import InternalCodesApiBook
import fastapi

class BookException(BaseApiRestException):
    GENERAL_ERROR_CODE = InternalCodesApiBook.BOOK_API_ERROR
    GENERAL_STATUS_CODE_HTTP = fastapi.status.HTTP_400_BAD_REQUEST