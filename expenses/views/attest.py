import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.models import Expense, ExpensePart, Person


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class AttestViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        expenses__to_attest = []

        # Add all expenses that the user may attest
        for expense in Expense.objects.filter(expensepart__attested_by__isnull=True).distinct():
            if may_attest_expense(expense, request):
                expenses__to_attest.append(expense.to_dict())

        return Response({'Expenses': expenses__to_attest})

    def create(self, request, **kwargs):
        expense_parts_to_be_saved = []
        if 'json' not in request.POST:
            return HttpResponseBadRequest()

        expense_part_ids = json.loads(request.POST['json'])['parts']

        for exp_part_id in expense_part_ids:
            try:
                part = ExpensePart.objects.get(id=exp_part_id)
            except ObjectDoesNotExist as e:
                return Response(
                    {'error:': "Expense_part with id " + str(e) + " does not exist"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if has_permission("attest-*", request) or \
                    has_permission("attest-" + part.budget_line.cost_centre.committee.name, request):

                if part.attested_by is None:
                    part.attested_by = Person.objects.get(user=request.user)
                    part.attest_date = date.today()
                    expense_parts_to_be_saved.append(part)
            else:
                return Response(
                    {'error': "You don't have permission to attest part with id " + str(part.id)},
                    status=status.HTTP_403_FORBIDDEN
                )
        for part in expense_parts_to_be_saved:
            part.save()

        return Response(status=status.HTTP_200_OK)


# Helper method
def may_attest_expense(exp, request):
    if has_permission("attest-*", request):
        return True

    for part in ExpensePart.objects.filter(expense=exp):
        if has_permission("attest-" + part.budget_line.cost_centre.committee.name, request):
            return True

    return False
