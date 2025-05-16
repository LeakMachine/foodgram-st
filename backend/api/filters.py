from django_filters import rest_framework as filters
from django_filters import DateFilter, DateFromToRangeFilter
from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_in_shopping_cart'
    )
    author = filters.NumberFilter(field_name='author__id')
    pub_date = DateFilter(field_name='created_at', lookup_expr='date')
    pub_date_after = DateFilter(field_name='created_at', lookup_expr='gte')
    pub_date_before = DateFilter(field_name='created_at', lookup_expr='lte')
    pub_date_range = DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Recipe
        fields = [
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'pub_date',
            'pub_date_after',
            'pub_date_before',
            'pub_date_range',
        ]

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    def filter_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(shopping_cart_items__user=user)
        return queryset.exclude(shopping_cart_items__user=user)


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
