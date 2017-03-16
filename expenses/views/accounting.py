import json

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.models import Expense


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class AccountingViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        expenses__ready_for_accounting = []

        # Add all expenses that the user will do accounting for
        for expense in Expense.objects.filter(
                        expensepart__attested_by__isnull=False,
                        reimbursement__isnull=False
                ).distinct():
            if may_account(expense, request):
                expenses__ready_for_accounting.append(expense.to_dict())

        return Response({'Expenses': expenses__ready_for_accounting})

    def create(self, request, **kwargs):
        json_arg = json.loads(request.POST['json'])

        try:
            exp = Expense.objects.get(id=int(json_arg['expense']))

            if may_account(exp,request):
                exp.verification = json_arg['verification_number']
                exp.save()
                return Response({'status': 'Success!'})
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except KeyError as e:
            return Response({'error': 'Json object is missing the field ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({'error': str(e) + ' is not a valid expense id'}, status=status.HTTP_400_BAD_REQUEST)


# Helper function
def may_account(exp,request):
    if has_permission("accounting-*", request):
        return True
    for part in exp.expensepart_set.all():
        if has_permission("accounting-" + part.budget_line.cost_centre.committee.name, request):
            return True

    return False
