from rest_framework.pagination import (
    PageNumberPagination,
    LimitOffsetPagination
)


class LimitPageNumberPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'limit'


class RecipePagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
