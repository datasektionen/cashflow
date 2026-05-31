from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework.exceptions import APIException

from .serializers import ProblemDetailSerializer


def problems(*exceptions: type[APIException]) -> OpenApiResponse:
    """Works like `problem` but enables multiple exceptions for the same HTTP code."""
    instances = [exc() for exc in exceptions]
    return OpenApiResponse(
        response=ProblemDetailSerializer,
        description=", ".join(f"`{i.default_code}`" for i in instances),
        examples=[
            OpenApiExample(
                name=instance.default_code,
                response_only=True,
                value={
                    "type": "about:blank",
                    "title": getattr(instance, "title", str(instance.default_detail)),
                    "detail": str(instance.default_detail),
                    "status": instance.status_code,
                    "code": instance.default_code,
                },
            )
            for instance in instances
        ],
    )


def problem(exception: type[APIException]) -> OpenApiResponse:
    """Helper function to annotate error responses for the OpenAPI schema.

    Will also include an example response based on the drf_problem format.

    Example::

        @extend_schema(responses={404: problem(NotFound)})
        def retrieve(self, request, pk):
            ...
    """
    instance = exception()
    return OpenApiResponse(
        response=ProblemDetailSerializer,
        description=f"{instance.default_detail} (code: `{instance.default_code}`)",
        examples=[
            OpenApiExample(
                name=instance.default_code,
                response_only=True,
                value={
                    "type": "about:blank",
                    "title": getattr(instance, "title", str(instance.default_detail)),
                    "detail": str(instance.default_detail),
                    "status": instance.status_code,
                    "code": instance.default_code,
                },
            )
        ],
    )
