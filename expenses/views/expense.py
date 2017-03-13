from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView, Response

from expenses.models import Expense


class ExpenseView(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    """
    List all expenses the current user can access
    """
    def get(self, request, format=None):
        return Response({'expenses': [exp.to_dict() for exp in Expense.objects.filter(owner__user=request.user)]})

