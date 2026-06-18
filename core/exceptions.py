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


class FlaggedAttestationError(AttestationError):
    pass


class ConfirmationError(Exception):
    pass


class UnauthorizedConfirmationError(ConfirmationError):
    pass


class NotConfirmableError(ConfirmationError):
    pass


class FlaggedConfirmationError(NotConfirmableError):
    pass


class DuplicateConfirmationError(ConfirmationError):
    pass


class UnauthorizedUnconfirmationError(ConfirmationError):
    pass


class NotConfirmedError(ConfirmationError):
    pass


class AccountingError(Exception):
    pass


class UnauthorizedAccountingError(AccountingError):
    pass


class AlreadyAccountedError(AccountingError):
    pass


class FortnoxRecordMissingError(AccountingError):
    pass


class CashflowVerificationMissingError(AccountingError):
    pass


class PaymentError(Exception):
    pass


class UnauthorizedPaymentError(PaymentError):
    pass
