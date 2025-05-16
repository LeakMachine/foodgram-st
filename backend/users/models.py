from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


EMAIL_LENGTH = 254
USERNAME_LENGTH = 150
NAME_LENGTH = 150


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Поле email обязательно")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class FoodgramUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=EMAIL_LENGTH)
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message="Недопустимые символы в имени пользователя."
            )
        ],
        error_messages={
            "unique": "Такой пользователь уже существует."
        }
    )
    profile_image = models.ImageField(upload_to="users/avatars/", blank=True)
    following = models.ManyToManyField(
        "self",
        through="Subscription",
        symmetrical=False,
        related_name="followers"
    )

    first_name = models.CharField(
        max_length=NAME_LENGTH,
        blank=False,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=NAME_LENGTH,
        blank=False,
        verbose_name="Фамилия"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        ordering = ("-date_joined",)

    objects = UserManager()

    def symbolCheck(self):
        if not re.match(r"^[\w.@+-]+\Z", self.username):
            raise ValidationError(
                "Недопустимые символы в имени пользователя."
            )

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="subscribers"
    )
    subscriber = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscription"
            )
        ]

    def __str__(self):
        return f'{self.subscriber.username} -> {self.author.username}'
