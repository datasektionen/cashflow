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
import base64
import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from expenses.csrfexemptauth import CsrfExemptSessionAuthentication
from expenses.models import Expense, File


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class FileViewSet(GenericViewSet):
    """
    Performs actions on files
    """
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BaseSerializer

    def create(self, request, **kwargs):
        """
        Create a new file

        :param request:     HTTP request
        """
        try:
            exp = Expense.objects.get(id=int(request.POST['expense']))

            if exp.owner.user is request.user or True:
                # noinspection PyShadowingBuiltins
                file = File(expense=exp, file=request.FILES['file'])
                file.save()
                return JsonResponse({'file': file.to_dict()})
            else:
                return JsonResponse({'error': "You don't own that expense"}, status=403)
        except KeyError as e:
            if 'file' in request.POST:
                # Probably has base64-file from android
                data = ContentFile(base64.b64decode(request.POST['file']), name='temp.png')
                file = File(expense=exp, file=data)
                file.save()
                return JsonResponse({'file': file.to_dict()})
            print(request.POST['file'])
            return JsonResponse({'error': 'Json object is missing the field ' + str(e)}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e) + ' is not a valid expense id'}, status=400)

    def destroy(self, request, pk, **kwargs):
        """
        Delete the file with the provided ID

        :param request:     HTTP request
        :param pk:          Comment ID to delete
        """
        # Retrieve file
        try:
            f = File.objects.get(pk=int(pk))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check if user is eligible to destroy it
        if f.expense.owner is request.user:
            f.delete()
            return Response(status=status.HTTP_200_OK)

        # If not, 403
        return Response(status=status.HTTP_403_FORBIDDEN)
