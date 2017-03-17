"""
      ______                       __         ______   __   ______
     /      \                     /  |       /      \ /  | /      \
    /$$$$$$  |  ______    _______ $$ |____  /$$$$$$  |$$ |/$$$$$$  | __   __   __
    $$ |  $$/  /      \  /       |$$      \ $$ |_ $$/ $$ |$$$  \$$ |/  | /  | /  |
    $$ |       $$$$$$  |/$$$$$$$/ $$$$$$$  |$$   |    $$ |$$$$  $$ |$$ | $$ | $$ |
    $$ |   __  /    $$ |$$      \ $$ |  $$ |$$$$/     $$ |$$ $$ $$ |$$ | $$ | $$ |
    $$ \__/  |/$$$$$$$ | $$$$$$  |$$ |  $$ |$$ |      $$ |$$ \$$$$ |$$ \_$$ \_$$ |
    $$    $$/ $$    $$ |/     $$/ $$ |  $$ |$$ |      $$ |$$   $$$/ $$   $$   $$/
     $$$$$$/   $$$$$$$/ $$$$$$$/  $$/   $$/ $$/       $$/  $$$$$$/   $$$$$/$$$$/

    File name: comments.py
    Authors: Alexander Viklund <viklu@kth.se>
             Mauritz Zachrisson <mauritzz@kth.se>
    Python version: 3.5
"""

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
    Performs actions on comments
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BaseSerializer

    def retrieve(self, request, pk, **kwargs):
        """
        Returns a JSON representation of the comment with the specified ID

        :param request:     HTTP request
        :param pk:          Comment ID
        """
        # Retrieve comment
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Ensure permission
        if may_view_expense(c.expense, request):
            return Response({'comment': c.to_dict()})
        return Response(status=status.HTTP_403_FORBIDDEN)

    def create(self, request, **kwargs):
        """
        Create a new comment from a JSON ID with the Expense ID and the content of the comment

        :param request:     HTTP request
        """
        # Build Comment object from JSON
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

        # Save to DB and give 201 response
        c.save()
        return Response({'comment': c.to_dict()}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk, **kwargs):
        """
        Update the comment with the specified id with the content from a JSON object

        :param request:     HTTP request
        :param pk:          Comment ID to update
        """
        # Retrieve comment
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if c.author.user is not request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Modify its contents
        try:
            json_args = request.data
            if 'content' in json_args:
                c.content = json_args['content']
            c.save()
            return Response({'comment': c.to_dict()})
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk, **kwargs):
        """
        Delete the comment with the provided ID

        :param request:     HTTP request
        :param pk:          Comment ID to delete
        """
        # Retrieve comment
        try:
            c = Comment.objects.get(id=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if user is eligible to destroy it
        if c.author is request.user or has_permission("admin", request):
            c.delete()
            return Response(status=status.HTTP_200_OK)

        # If not, 403
        return Response(status=status.HTTP_403_FORBIDDEN)
