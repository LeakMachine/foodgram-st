from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from users.models import FoodgramUser, Subscription
from recipes.models import Recipe, Ingredient, RecipeIngredient
from drf_extra_fields.fields import Base64ImageField
from django.core.validators import RegexValidator
from django.contrib.auth import authenticate


USERNAME_LENGTH = 150
NAME_LENGTH = 150


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать минимум 8 символов"
            )
        return value


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            email=attrs.get('email'),
            password=attrs.get('password')
        )
        if not user:
            raise serializers.ValidationError("Неверные учетные данные")
        attrs['user'] = user
        return attrs


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class FoodgramUserCreateSerializer(UserCreateSerializer):
    username = serializers.CharField(
        max_length=USERNAME_LENGTH,
        required=True,
        validators=[RegexValidator(
            r'^[\w.@+-]+\Z',
            "Недопустимые символы в имени пользователя."
        )]
    )
    first_name = serializers.CharField(
        max_length=NAME_LENGTH,
        required=True, allow_blank=False, trim_whitespace=True
    )
    last_name = serializers.CharField(
        max_length=NAME_LENGTH,
        required=True, allow_blank=False, trim_whitespace=True
    )

    class Meta(UserCreateSerializer.Meta):
        model = FoodgramUser
        fields = (
            "id", "email", "username", "first_name", "last_name", "password"
        )
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        pwd = data.get('password')
        if pwd and len(pwd) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать минимум 8 символов"
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FoodgramUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            return request.build_absolute_uri(
                obj.profile_image.url
            ) if request else obj.profile_image.url
        return None


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                author=obj, subscriber=request.user
            ).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            return request.build_absolute_uri(
                obj.profile_image.url
            ) if request else obj.profile_image.url
        return None


class IngredientAmountWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество должно быть больше 0'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    recipe_ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source="components"
    )
    ingredients = IngredientAmountWriteSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(max_length=256)
    text = serializers.CharField()

    class Meta:
        model = Recipe
        fields = (
            "id", "author", "recipe_ingredients", "ingredients",
            "is_favorited", "is_in_shopping_cart", "name",
            "image", "text", "cooking_time",
        )
        read_only_fields = (
            "id", "author", "is_favorited", "is_in_shopping_cart",
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Поле изображения обязательно.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.partial:
            required_fields = {"ingredients", "name", "text", "cooking_time"}
            sent = set(self.initial_data.keys())
            missing = required_fields - sent
            if missing:
                errors = {field: [
                    "Это поле обязательно для update."
                ] for field in missing}
                raise serializers.ValidationError(errors)
        else:
            data_keys = set(self.initial_data.keys())

            if not self.instance and "image" not in data_keys:
                raise serializers.ValidationError(
                    {"image": ["Это поле обязательно."]}
                )

            if self.instance and self.context[
                "request"
            ].method == "PUT" and "image" not in data_keys:
                raise serializers.ValidationError(
                    {"image": ["Это поле обязательно для PUT."]}
                )
            if "ingredients" not in data_keys:
                raise serializers.ValidationError(
                    {"ingredients": ["Это поле обязательно."]}
                )
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["ingredients"] = IngredientInRecipeSerializer(
            instance.components.all(), many=True, context=self.context
        ).data
        if "recipe_ingredients" in representation:
            representation.pop("recipe_ingredients")
        return representation

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_cart_items.filter(user=request.user).exists()

    def _manage_ingredients(self, recipe, ingredients_data_list):
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        ings_to_create = [
            RecipeIngredient(
                recipe=recipe, ingredient=item_data["id"],
                amount=item_data["amount"],
            )
            for item_data in ingredients_data_list
        ]
        RecipeIngredient.objects.bulk_create(ings_to_create)

    def create(self, validated_data):
        ingredients_list = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._manage_ingredients(recipe, ingredients_list)
        return recipe

    def update(self, instance, validated_data):
        ingredients_list = validated_data.pop("ingredients", [])
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.image = validated_data.get("image", instance.image)
        instance.save()

        self._manage_ingredients(instance, ingredients_list)

        return instance

    def validate_ingredients(self, data):
        if not data:
            raise serializers.ValidationError(
                "Пожалуйста, укажите ингредиенты."
            )
        ids = [item["id"] for item in data]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        for item in data:
            amount = item.get("amount")
            if not isinstance(amount, int) or amount < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть больше нуля."
                )
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed',
            'avatar', 'recipes_count', 'recipes',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscriber=request.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        author = obj.author
        qs = Recipe.objects.filter(author=author)
        limit = self.context.get('request').query_params.get('recipes_limit')
        if limit is not None:
            try:
                limit = int(limit)
                qs = qs[:limit]
            except (ValueError, TypeError):
                pass
        return RecipeMinifiedSerializer(
            qs, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_avatar(self, obj):
        author = obj.author
        if not author.profile_image:
            return None
        request = self.context.get('request')
        url = author.profile_image.url
        return request.build_absolute_uri(url) if request else url
