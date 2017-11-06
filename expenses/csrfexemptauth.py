from rest_framework.authentication import SessionAuthentication

"""
Settings for removing csrf checks for APIs.
"""
class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # Disable CSRF check for API requests
