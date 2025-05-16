from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    RecipeViewSet,
    IngredientViewSet,
    LoginView,
    LogoutView,
    redirect_short_link,
)
from django.conf.urls.static import static
from django.conf import settings


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),

    path('users/set_password/', UserViewSet.as_view({'post': 'set_password'})),
    path('auth/token/login/', LoginView.as_view(), name='token_login'),
    path('auth/token/logout/', LogoutView.as_view(), name='token_logout'),

    path(
        's/<str:short_link>/', redirect_short_link, name='redirect_short_link'
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
