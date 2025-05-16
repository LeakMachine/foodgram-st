from django.db import models
from django.core.validators import MinValueValidator
from users.models import FoodgramUser
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='components'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='used_in'
    )
    amount = models.PositiveSmallIntegerField(
        "Количество", validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Компонент рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]


class Recipe(models.Model):
    name = models.CharField('Название', max_length=256, unique=True)
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='authored_recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        related_name='recipes'
    )
    image = models.ImageField('Изображение', upload_to='recipes/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время готовки (мин)',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        'Дата и время публикации', auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        ordering = ('-pub_date',)

    @property
    def favorites_count(self):
        return self.favorite_set.count()

    def __str__(self):
        return self.label


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart_items'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='shopping_cart_items'
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        unique_together = ('user', 'recipe')
