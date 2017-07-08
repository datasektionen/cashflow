import json

from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.models import Expense, Payment, Profile


# noinspection PyUnusedLocal,PyMethodMayBeStatic
class PaymentViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, **kwargs):
        if has_permission("admin", request):
            return Response({
                'payments': [payment.to_dict() for payment in Payment.objects.all()]
            })
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def create(self, request, **kwargs):
        if has_permission("pay", request.user):
            try:
                json_args = json.loads(request.POST['json'])
                total = 0
                for exp_id in json_args['expense_ids']:
                    total += Expense.objects.get(id=exp_id).compute_total()

                payment = Payment(
                    date=date.today(),
                    payer=Profile.objects.get(user=request.user),
                    receiver=Expense.objects.get(id=json_args['expense_ids'][0]).owner,
                    account_id=json_args['account_id'],
                    sum=total
                )

                payment.save()

                for exp_id in json_args['expense_ids']:
                    exp = Expense.objects.get(id=exp_id)
                    exp.reimbursement = payment
                    exp.save()

            except KeyError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, pk, **kwargs):
        try:
            payments = Payment.objects.get(id=int(pk), receiver__user=request.user)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(payments.to_dict())

    @list_route()
    def ready_for_payment(self, request, **kwargs):
        expenses = []

        # Retrieve all expenses which are not reimbursed
        to_be_paid_expenses = Expense.objects.filter(reimbursement__isnull=True)

        # Filter out the expenses with all parts attested
        for expense in to_be_paid_expenses:
            if len(expense.expensepart_set.filter(attested_by__isnull=True)) == 0:  # All parts attested
                expenses.append(expense.to_dict())

        return JsonResponse({'ready_for_payment': expenses})
