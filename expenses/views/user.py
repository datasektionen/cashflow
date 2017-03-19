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

    File name: user.py
    Authors: Alexander Viklund <viklu@kth.se>
             Mauritz Zachrisson <mauritzz@kth.se>
    Python version: 3.5
"""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from cashflow.dauth import has_permission
from expenses.csrfexemptauth import CsrfExemptSessionAuthentication
from expenses.models import Person, Payment


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class UserViewSet(GenericViewSet):
    """
    Performs operations on Persons (user objects)
    """
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BaseSerializer
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-z]+'

    def list(self, request, **kwargs):
        """
        List all usernames

        :param request:     HTTP request
        """
        return Response({'users': User.objects.all().values('username')})

    def retrieve(self, request, username, **kwargs):
        """
        Returns a JSON representation of the user with the specified username

        :param request:     HTTP request
        :param username:    Username to retrieve
        """
        # Retrieve user
        try:
            person = Person.objects.get(user__username=username)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if person.user.username == request.user.username or has_permission("pay", request):
            return Response({'user': person.to_dict()})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @list_route()
    def current(self, request, **kwargs):
        """
        Returns a JSON representation of the current user

        :param request:     HTTP request
        """
        return Response({'user': Person.objects.get(user=request.user).to_dict()})

    def partial_update(self, request, username, **kwargs):
        """
        Update the user with the specified id with the bank information and settings from a JSON object

        :param request:     HTTP request
        :param username:    Username to update
        """
        # Retrieve user
        try:
            person = Person.objects.get(user__username=username)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check permissions
        if person.user.username != request.user.username:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Update affected fields
        try:
            json_args = request.data

            if 'bank_account' in json_args:
                person.bank_account = json_args['bank_account']
            if 'sorting_number' in json_args:
                person.sorting_number = json_args['sorting_number']
            if 'bank_name' in json_args:
                person.bank_name = json_args['bank_name']
            if 'default_account' in json_args:
                person.default_account_id = json_args['default_account']

            person.save()
            return Response({'user': person.to_dict()})
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def payments(self, request, username, **kwargs):
        if request.user.username is username or has_permission("admin", request):
            return Response({
                'payments': [payment.to_dict() for payment in Payment.objects.filter(receiver__user__username=username)]
            })
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
