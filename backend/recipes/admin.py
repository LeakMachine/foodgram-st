from django.contrib import admin
from .models import (
    Ingredient, RecipeIngredient, Recipe, ShoppingCart, Favorite
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('author',)
    search_fields = ('name', 'text')
    inlines = (RecipeIngredientInline,)
    date_hierarchy = 'pub_date'

    def favorites_count(self, obj):
        return obj.favorite_set.count()
    favorites_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )

    autocomplete_fields = ('user', 'recipe')

    def has_add_permission(self, request):
        return super().has_add_permission(request)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )

    autocomplete_fields = ('user', 'recipe')
