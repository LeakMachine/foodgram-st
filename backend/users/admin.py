from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import FoodgramUser, Subscription


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = ("email", "username", "is_staff")
    search_fields = ("email", "username")
    readonly_fields = ("date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Персональные данные", {"fields": ("username", "profile_image")}),
        ("Права", {"fields": ("is_active", "is_staff")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("author", "subscriber", "created_at")
    search_fields = ("author", "subscriber")
    readonly_fields = ("created_at",)
