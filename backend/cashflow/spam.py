import requests
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from cashflow import settings
from expenses.models import Expense, Comment
from invoices.models import Invoice

from structlog import get_logger

from notifications import NotificationProvider

logger = get_logger(__name__)


def send_mail(recipient, subject, content):
    logger.debug(
        "sending mail", recipient=recipient, subject=subject, content=content[:100]
    )
    requests.post(
        settings.SPAM_URL + "/api/legacy/sendmail",
        json={
            "from": "cashflow-no-reply@datasektionen.se",
            "to": recipient,
            "subject": subject,
            "content": content,
            "key": settings.SPAM_API_KEY,
        },
    )


class SpamMail(NotificationProvider):

    def on_invoice_update(self, invoice):
        raise NotImplementedError()

    def on_comment(self, claim: Expense | Invoice, comment: Comment):

        recipient = claim.owner.user.email
        subject = str(comment.author) + " har lagt till en kommentar på ditt utlägg."

        if isinstance(claim, Expense):
            kind = "expenses"
        elif isinstance(claim, Invoice):
            kind = "invoices"
        else:
            raise ValueError("Invalid claim type")

        link = f"{settings.FRONTEND_URL}/{claim.owner.user.username}/{kind}/{claim.id}"
        content = render_to_string(
            "email.html", {"comment": comment, "receiver": claim.owner, "link": link}
        )
        send_mail(recipient, subject, content)

    def on_attest(self, claim: Expense | Invoice, attester: User):
        raise NotImplementedError()

    def on_confirm(self, expense: Expense, confirmer: User):
        raise NotImplementedError()

    def on_payment(self, claim: Expense | Invoice, payer: User):
        raise NotImplementedError()

    def on_expense_update(self, expense):
        raise NotImplementedError()
