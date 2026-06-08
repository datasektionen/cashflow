from rest_framework import status
from rest_framework.exceptions import APIException


class ErrorToDictMixin:
    # (!) The following methods are meant as a "compatability" layer to allow these exceptions to work with
    # normal Django views, before we switch over to DRF only

    def to_dict(self) -> dict:
        return {
            "type": f"/problems/{self.default_code}",
            "title": self.title,
            "detail": self.detail,
            "status_code": self.status_code,
        }


class AttestationError(Exception):
    pass


class SelfAttestationError(AttestationError):
    pass


class UnauthorizedAttestationError(AttestationError):
    pass


class EmptyCommentError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A comment cannot be blank or consist only of whitespace."
    default_code = "empty_comment"
    default_title = "Empty comment"
