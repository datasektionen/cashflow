import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from expenses.models import Expense, ExpensePart, Profile


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class AttestViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        expenses__to_attest = []

        # Add all expenses that the user may attest
        for expense in Expense.objects.filter(expensepart__attested_by__isnull=True).distinct():
            parts = ExpensePart.objects.filter(expense=exp)

            if any(request.user.profile.may_attest(ep) for ep in parts):
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

            if request.user.profile.may_attest(part):
                if part.attested_by is None:
                    part.attested_by = Profile.objects.get(user=request.user)
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
