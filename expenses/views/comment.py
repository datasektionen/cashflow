import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.models import Comment
from expenses.views.expense import may_view_expense


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class CommentViewSet(GenericViewSet):
    """
    retrieve:
    Returns a json representation of the comment with the specified id

    create:
    Create a new comment from a json-object with the expense-id and the content of the comment

    partial-update:
    Update the comment with the specified id with the content from a json-object

    destroy:
    Delete the comment with the provided id
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BaseSerializer

    def retrieve(self, request, pk, **kwargs):
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if may_view_expense(c.expense, request):
            return Response({'comment': c.to_dict()})
        return Response(status=status.HTTP_403_FORBIDDEN)

    def create(self, request, **kwargs):
        try:
            json_args = json.loads(request.POST['json'])

            c = Comment(
                expense_id=json_args['expense'],
                author=request.user,
                date=date.today(),
                content=json_args['content']
            )
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        c.save()
        return Response({'comment': c.to_dict()}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk, **kwargs):
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if c.author.user is not request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            json_args = json.loads(request.PATCH['json'])
            if 'content' in json_args:
                c.content = json_args['content']
            c.save()
            return Response({'comment': c.to_dict()})
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk, **kwargs):
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if c.author is request.user or has_permission("admin", request):
            c.delete()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
