from typing import Any, TypedDict, Unpack

from django.db.models import Case, QuerySet, When
from rapidfuzz import fuzz, process

lazy from core.api.filters import apply_claim_filters
lazy from core.models import ClaimQuerySet

SCORE_CUTOFF = 80.0


def fuzzy_model_search[QS: QuerySet[Any]](
    queryset: QS,
    query: str,
    field: str,
    partial: bool = True,
    pk_field: str = "id",
    score_cutoff: float = SCORE_CUTOFF,
) -> QS:
    """Performs a fuzzy search on a model queryset.

    Fetches all objects and is therefore not very efficient, should only be used in dedicated search functions.
    Results are ordered by match score, best match first.

    :param partial: whether to perform a partial (contains) search
    :param queryset: queryset to search
    :param query: query string
    :param field: field to search
    :param pk_field: primary key/lookup field, this is used to fetch the matches from the original queryset
    :param score_cutoff: score cutoff (0.0 - 100.0) for rapidfuzz (higher means more strict matching)
    """
    hay = queryset.values_list(pk_field, field, named=True)
    matches = process.extract(
        query.lower(),
        hay,
        limit=None,
        score_cutoff=score_cutoff,
        scorer=fuzz.partial_ratio if partial else fuzz.WRatio,
        processor=lambda x: (
            x.lower() if isinstance(x, str) else getattr(x, field).lower()
        ),
    )
    ids = [getattr(row, pk_field) for row, _score, _index in matches]
    preserved_order = Case(
        *[When(**{pk_field: pk}, then=rank) for rank, pk in enumerate(ids)]
    )
    return queryset.filter(**{f"{pk_field}__in": ids}).order_by(preserved_order)


class ClaimSearchFields(TypedDict, total=False):
    description: str | None
    description_fuzzy: str | None


def claim_search(
    queryset: ClaimQuerySet, **search_fields: Unpack[ClaimSearchFields]
) -> ClaimQuerySet:
    filtered = apply_claim_filters(queryset, dict(search_fields), user=None)

    for key, value in search_fields.items():
        match key, value:
            case "description", str():
                filtered = filtered.filter(description__icontains=value)
            case "description_fuzzy", str():
                return fuzzy_model_search(filtered, value, "description")

    return filtered
