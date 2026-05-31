from rest_framework.exceptions import APIException


class InvalidExpenseDateError(APIException):
    status_code = 422
    title = "Invalid expense date"
    default_detail = "Invalid expense date, cannot be in the future."
    default_code = "invalid_expense_date"
