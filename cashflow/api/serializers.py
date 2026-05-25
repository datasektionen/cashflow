from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, ListField


class CostCentreSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    type = CharField(read_only=True)


class SecondaryCostCentreSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    cost_centre_id = IntegerField(source="cc_id", read_only=True)


class BudgetLineSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    secondary_cost_centre_id = IntegerField(source="scc_id", read_only=True)
    accounts = ListField(child=IntegerField(), read_only=True)
    income = IntegerField(read_only=True)
    expense = IntegerField(read_only=True)
    comment = CharField(read_only=True)
