import requests
from cashflow import settings

def send_mail(recipient, subject, content):
    if not settings.SEND_EMAILS:
        return

    requests.post(settings.SPAM_URL + '/api/sendmail', json={
        'from': 'no-reply@datasektionen.se',
        'to': recipient,
        'subject': subject,
        'content': content,
        'key': settings.SPAM_API_KEY
    })
