from django.conf import settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class FeaturesList(APIView):
    @extend_schema(
        summary="List enabled features",
        description="Returns true/false for which optional features are enabled on this instance.",
        operation_id="list_features",
        tags=["Features"],
        responses=inline_serializer(
            name="Features",
            fields={"fortnox": serializers.BooleanField()},
        ),
    )
    def get(self, request):
        return Response({"fortnox": settings.FORTNOX_ENABLED})
