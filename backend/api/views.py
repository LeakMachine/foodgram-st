from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework import viewsets, filters, status, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter, IngredientFilter
import io
from reportlab.pdfgen import canvas
from django.db import models
from users.models import Subscription, FoodgramUser
from recipes.models import Recipe, Ingredient, ShoppingCart, Favorite
from .models import ShortLink
from .serializers import (
    FoodgramUserCreateSerializer,
    FoodgramUserSerializer,
    RecipeSerializer,
    RecipeMinifiedSerializer,
    SubscriptionSerializer,
    IngredientSerializer,
    AvatarSerializer,
    SetPasswordSerializer,
    EmailAuthTokenSerializer,
)
from .pagination import LimitPageNumberPagination, RecipePagination


def redirect_short_link(request, short_link):
    link = get_object_or_404(ShortLink, key=short_link)
    return redirect(f'/api/recipes/{link.recipe.id}/')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = EmailAuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    queryset = FoodgramUser.objects.all()
    pagination_class = LimitPageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_serializer_class(self):
        if self.action == 'create':
            return FoodgramUserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return FoodgramUserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action in [
            'me', 'set_password', 'subscribe', 'subscriptions', 'avatar'
        ]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    @action(
        detail=False, methods=['get'], permission_classes=[
            permissions.IsAuthenticated
        ], url_path='me'
    )
    def me(self, request):
        return Response(FoodgramUserSerializer(
            request.user, context={'request': request}
        ).data)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': [
                    'Неверный пароль.'
                ]}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(FoodgramUser, pk=pk)
        if author == request.user:
            return Response(
                {"detail": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            sub, created = Subscription.objects.get_or_create(
                subscriber=request.user, author=author
            )
            if not created:
                return Response(
                    {"detail": "Вы уже подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                sub, context={
                    'request':
                        request, 'recipes_limit': request.query_params.get(
                                 'recipes_limit'
                        )
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        qs = Subscription.objects.filter(
            subscriber=request.user, author=author
        )
        if not qs.exists():
            return Response(
                {"detail": "Подписка не найдена."},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        qs = Subscription.objects.filter(subscriber=request.user)
        paginated = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(
            paginated,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[
        permissions.IsAuthenticated
    ], url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if user.profile_image:
                user.profile_image.delete(save=False)
            user.profile_image = serializer.validated_data['avatar']
            user.save()
            avatar_url = request.build_absolute_uri(user.profile_image.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        if user.profile_image:
            user.profile_image.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    search_fields = ['name', 'author__username']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        if "image" not in request.data:
            return Response(
                {"image": ["Это поле обязательно."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "У вас нет прав для изменения этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "У вас нет прав для удаления этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'], permission_classes=[
        permissions.AllowAny
    ], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe=recipe
        )
        absolute_url = request.build_absolute_uri(
            short_link.get_absolute_url()
        )
        return Response({
            'short-link': absolute_url
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[
        permissions.IsAuthenticated
    ], url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        fav_qs = Favorite.objects.filter(user=request.user, recipe=recipe)

        if request.method == 'POST':
            if fav_qs.exists():
                return Response({
                    'detail': 'Уже в избранном'
                }, status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeMinifiedSerializer(
                    recipe
                ).data, status=status.HTTP_201_CREATED
            )

        if not fav_qs.exists():
            return Response({
                'detail': 'Не в избранном'
            }, status=status.HTTP_400_BAD_REQUEST)
        fav_qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        cart_qs = ShoppingCart.objects.filter(user=request.user, recipe=recipe)

        if request.method == 'POST':
            if cart_qs.exists():
                return Response(
                    {"detail": "Рецепт уже в корзине."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            data = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        if not cart_qs.exists():
            return Response(
                {"detail": "Рецепта нет в корзине."},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[
        permissions.IsAuthenticated
    ], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = Ingredient.objects.filter(
            used_in__recipe__shopping_cart_items__user=request.user
        ).values(
            'name', 'measurement_unit'
        ).annotate(total=models.Sum('used_in__amount'))

        lines = [
            f"{i['name']} ({i['measurement_unit']}) — {i['total']}"
            for i in ingredients
        ]
        fmt = request.query_params.get('format', 'txt')

        if fmt == 'pdf':
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer)
            y = 800
            for line in lines:
                p.drawString(50, y, line)
                y -= 15
            p.showPage()
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response[
                'Content-Disposition'
            ] = 'attachment; filename="shopping_list.pdf"'
            return response

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response
