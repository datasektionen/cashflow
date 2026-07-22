from drf_spectacular.plumbing import build_mock_request
from rest_framework.test import APIRequestFactory


def get_mock_request(method, path, view, original_request, **kwargs):
    """Wraps drf_spectacular's build_mock_request to support HTTP methods that
    APIRequestFactory has no dedicated helper for (e.g. the QUERY method used
    by the expense/invoice search actions).
    """
    if not hasattr(APIRequestFactory(), method.lower()):
        request = APIRequestFactory().generic(method, path)
        request = view.initialize_request(request)
        if original_request:
            request.user = original_request.user
            request.auth = original_request.auth
        return request

    return build_mock_request(method, path, view, original_request, **kwargs)
