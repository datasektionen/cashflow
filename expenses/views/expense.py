import json

from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.models import Expense, ExpensePart


# noinspection PyUnusedLocal,PyMethodMayBeStatic
class ExpenseViewSet(GenericViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    """
    List all expenses the current user can access
    """
    def list(self, request, **kwargs):
        return Response({'expenses': [exp.to_dict() for exp in Expense.objects.filter(owner__user=request.user)]})

    def create(self, request, **kwargs):
        parts_to_be_saved = []
        try:
            json_args = json.loads(request.POST['json'])

            exp = Expense(
                owner=request.user,
                description=json_args['description'],
                expense_date=date(json_args['expense_date'])
            )

            for part in json_args['expense_parts']:
                p = ExpensePart(
                    expense=exp,
                    budget_line_id=part['budget_line_id'],
                    amount=part['amount']
                )
                parts_to_be_saved.append(p)
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        exp.save()
        for p in parts_to_be_saved:
            p.save()
        return Response({'expense', exp.to_dict()})

    def partial_update(self, request, pk, **kwargs):
        parts_to_be_saved = []

        try:
            exp = Expense.objects.get(id=int(pk), owner__user=request.user)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            json_args = json.loads(request.POST['json'])

            if 'description' in json_args:
                exp.description = json_args['description']
            if 'expense_date' in json_args:
                exp.expense_date = date(json_args['expense_date'])

            if 'expense_parts' in json_args:
                for part in json_args['expense_parts']:
                    if 'id' in part:
                        try:
                            p = ExpensePart.objects.get(id=part['id'], owner__user=request.user)
                        except ValueError as e:
                            return Response(status=status.HTTP_400_BAD_REQUEST)
                        except ObjectDoesNotExist as e:
                            return Response(status=status.HTTP_404_NOT_FOUND)

                        if 'budget_line_id' in part:
                            p.budget_line_id = part['budget_line_id']
                        if 'amount' in part:
                            p.amount = part['amount']
                    else:
                        p = ExpensePart(
                            expense=e,
                            budget_line_id=part['budget_line_id'],
                            amount=part['amount']
                        )
                    parts_to_be_saved.append(p)
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        exp.save()
        for p in parts_to_be_saved:
            p.save()
        return Response({'expense', exp.to_dict()})

    """
    Retrieve a single expense with parts and file information
    """
    def retrieve(self, request, pk, **kwargs):
        try:
            exp = Expense.objects.get(id=int(pk), owner__user=request.user)
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(exp.to_dict())

    """
    Remove expense based on ID.
    """
    def destroy(self, request, pk, **kwargs):
        try:
            exp = Expense.objects.get(id=int(pk))
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if request.user is exp.owner.user or has_permission("admin", request):
            exp.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @detail_route()
    def comments(self, request, pk, **kwargs):
        try:
            exp = Expense.objects.get(id=int(pk))
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if may_view_expense(exp, request):
            return Response({'comments': [comment.to_dict() for comment in exp.comment_set.all()]})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @detail_route()
    def files(self, request, pk, **kwargs):
        try:
            exp = Expense.objects.get(id=int(pk))
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if may_view_expense(exp, request):
            # noinspection PyShadowingBuiltins
            return Response({'files': [file.to_dict() for file in exp.file_set.all()]})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


def may_view_expense(exp, request):
    # Helper method
    if request.user is exp.owner:
        return True
    if has_permission("attest-*", request):
        return True

    for part in exp.expense_part_set.all():
        if has_permission("attest-" + part.budget_line.cost_centre.committee.name, request):
            return True

    return False
