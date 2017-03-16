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

    File name: file.py
    Authors: Alexander Viklund <viklu@kth.se>
             Mauritz Zachrisson <mauritzz@kth.se>
    Python version: 3.5
"""

import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from expenses.models import Expense, File


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class FileViewSet(GenericViewSet):
    """
    Performs actions on comments
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BaseSerializer

    def create(self, request, **kwargs):
        """
        Create a new comment from a JSON ID with the Expense ID and the content of the comment

        :param request:     HTTP request
        """
        # Build Comment object from JSON
        json_arg = json.loads(request.POST['json'])

        try:
            exp = Expense.objects.get(id=int(json_arg['expense']))

            if exp.owner.user is request.user:
                # noinspection PyShadowingBuiltins
                file = File(belonging_to=exp, file=request.FILES['file'])
                file.save()
                return JsonResponse({'file': file.to_dict()})
            else:
                return JsonResponse({'error': "You don't own that expense"}, status=403)
        except KeyError as e:
            return JsonResponse({'error': 'Json object is missing the field ' + str(e)}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e) + ' is not a valid expense id'}, status=400)

    def destroy(self, request, pk, **kwargs):
        """
        Delete the comment with the provided ID

        :param request:     HTTP request
        :param pk:          Comment ID to delete
        """
        # Retrieve comment
        try:
            f = File.objects.get(pk=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if user is eligible to destroy it
        if f.belonging_to.owner is request.user:
            f.delete()
            return Response(status=status.HTTP_200_OK)

        # If not, 403
        return Response(status=status.HTTP_403_FORBIDDEN)
