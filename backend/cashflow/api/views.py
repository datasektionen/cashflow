from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class FeaturesList(APIView):
    def get(self, request):
        return Response({"fortnox": settings.FORTNOX_ENABLED})
