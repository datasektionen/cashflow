from django.db.models import Case, Model, QuerySet, When
from rapidfuzz import process, fuzz

SCORE_CUTOFF = 80.0


def fuzzy_model_search[T: Model](
    queryset: QuerySet[T],
    query: str,
    field: str,
    partial: bool = True,
    pk_field: str = "id",
    score_cutoff: float = SCORE_CUTOFF,
) -> QuerySet[T]:
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
