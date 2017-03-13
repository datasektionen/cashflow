from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import GenericViewSet

from expenses.models import Expense


# noinspection PyUnusedLocal
class ExpenseViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    """
    List all expenses the current user can access
    """
    def list(self, request, **kwargs):
        return Response({'expenses': [exp.to_dict() for exp in Expense.objects.filter(owner__user=request.user)]})

    """
    Retrieve a single expense with parts and file information
    """
    def retrieve(self, request, pk, **kwargs):
        try:
            exp = Expense.objects.get(id=int(pk))
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(exp.to_dict())

