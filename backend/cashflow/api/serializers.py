from typing import Any

from rest_framework import serializers
from rest_framework.fields import IntegerField, CharField, ListField, BooleanField
from structlog import get_logger

from cashflow.gordian import retrieve_account_from_gordian

logger = get_logger(__name__)


class PartRecommendationsMixin(metaclass=serializers.SerializerMetaclass):
    """Adds voucher recommendations derived from GOrdian + Fortnox to a part serializer.

    Recommendations are only populated when the view opts in via the
    `include_recommendations` serializer context (single-object reads); they
    are null in list responses to avoid a GOrdian lookup per part.
    """

    # Provided by the Serializer this mixin is combined with.
    context: dict[str, Any]

    recommended_accounts = serializers.SerializerMethodField(
        help_text=(
            "Fortnox account numbers derived from this part's GOrdian budget line, "
            "suggested when creating a voucher. Empty if the budget line can't be "
            "resolved on GOrdian; null in list responses."
        )
    )
    recommended_cost_centre = serializers.SerializerMethodField(
        help_text=(
            "Code of the Fortnox cost centre matching this part's GOrdian cost "
            "centre, suggested when creating a voucher. Null when no match is "
            "found, when the Fortnox integration is unavailable, or in list "
            "responses."
        )
    )

    def get_recommended_accounts(self, part) -> list[int] | None:
        if not self.context.get("include_recommendations"):
            return None
        try:
            return retrieve_account_from_gordian(part)
        except ValueError as e:
            logger.warning(
                "could not resolve recommended accounts for part",
                part_id=part.id,
                error=str(e),
            )
            return []

    def get_recommended_cost_centre(self, part) -> str | None:
        if not self.context.get("include_recommendations"):
            return None
        request = self.context.get("request")
        if request is None or getattr(request, "fortnox_service", None) is None:
            return None
        # Imported here to avoid a circular import: cashflow.utils imports the
        # expense/invoice models whose serializers use this mixin.
        from cashflow.utils import fortnox_cost_center_for_part

        try:
            cost_centre = fortnox_cost_center_for_part(request, part)
        except Exception as e:
            # Recommendations are best-effort decoration; a Fortnox hiccup
            # must not break the detail endpoint.
            logger.warning(
                "could not resolve recommended cost centre for part",
                part_id=part.id,
                error=str(e),
            )
            return None
        return cost_centre.Code if cost_centre is not None else None


class CostCentreSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    type = CharField(read_only=True)
    active = BooleanField(read_only=True)


class SecondaryCostCentreSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    cost_centre_id = IntegerField(source="cc_id", read_only=True)
    active = BooleanField(read_only=True)


class BudgetLineSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    name = CharField(read_only=True)
    secondary_cost_centre_id = IntegerField(source="scc_id", read_only=True)
    accounts = ListField(child=IntegerField(), source="account", read_only=True)
    income = IntegerField(read_only=True)
    expense = IntegerField(read_only=True)
    comment = CharField(read_only=True)
    active = BooleanField(read_only=True)
