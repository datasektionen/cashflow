from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Settings for removing csrf checks for APIs.
    """

    def enforce_csrf(self, request):
        return  # Disable CSRF check for API requests
