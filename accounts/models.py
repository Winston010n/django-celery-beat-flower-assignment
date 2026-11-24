from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Администратор"
        MODERATOR = "MODERATOR", "Модератор"
        USER = "USER", "Пользователь"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
