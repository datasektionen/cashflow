from django.core.paginator import Page
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.urls import remove_query_param, replace_query_param


class DefaultPagination(PageNumberPagination):
    """Pagination class that allows clients to customize per-page count."""

    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_next_path(self) -> str | None:
        assert isinstance(self.page, Page)
        assert isinstance(self.request, Request)
        if not self.page.has_next():
            return None
        path = self.request.get_full_path()
        return replace_query_param(
            path, self.page_query_param, self.page.next_page_number()
        )

    def get_previous_path(self) -> str | None:
        assert isinstance(self.page, Page)
        assert isinstance(self.request, Request)
        if not self.page.has_previous():
            return None
        path = self.request.get_full_path()
        previous_page = self.page.previous_page_number()
        return replace_query_param(path, self.page_query_param, previous_page)

    def get_paginated_response(self, data):
        assert isinstance(self.page, Page)
        assert isinstance(self.request, Request)
        return Response(
            {
                "data": data,
                "pagination": {
                    "total": self.page.paginator.count,
                    "page": self.page.number,
                    "per_page": self.get_page_size(self.request),
                    "total_pages": self.page.paginator.num_pages,
                    "next": self.get_next_path(),
                    "previous": self.get_previous_path(),
                },
            }
        )
