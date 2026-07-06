from drf_problems.utils import register_exception
from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidExpenseDateError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    title = "Invalid expense date"
    default_detail = "Invalid expense date, cannot be in the future."
    default_code = "invalid_expense_date"


register_exception(InvalidExpenseDateError)
