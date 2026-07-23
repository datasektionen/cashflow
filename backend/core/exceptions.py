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


class MismatchedTotalAmountError(AccountingError):
    pass


class NoAccountingMethodError(AccountingError):
    pass
