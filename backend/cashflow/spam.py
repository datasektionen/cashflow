import requests
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from structlog import get_logger

from cashflow import settings
from core.models import Claim, Comment
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

    def on_comment(self, claim: Claim, comment: Comment):

        recipient = claim.owner.user.email
        subject = str(comment.author) + " har lagt till en kommentar på ditt utlägg."

        link = f"{settings.FRONTEND_URL}/{claim.owner.user.username}/{claim.type + 's'}/{claim.data_id}"
        content = render_to_string(
            "email.html", {"comment": comment, "receiver": claim.owner, "link": link}
        )
        send_mail(recipient, subject, content)

    def on_attest(self, claim: Claim, attester: User):
        raise NotImplementedError()

    def on_confirm(self, claim: Claim, confirmer: User):
        raise NotImplementedError()

    def on_payment(self, claim: Claim, payer: User):
        raise NotImplementedError()

    def on_expense_update(self, expense):
        raise NotImplementedError()
