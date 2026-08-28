"""The `User` model, per docs/backend/db-schema.md.

Email is the sole login identifier: there is no username field and no
self-service signup endpoint anywhere in the spec (docs/backend/auth-contract.md
#user-model-and-account-creation) — accounts are provisioned out-of-band via
`manage.py createsuperuser` or the Django admin.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """`create_user`/`create_superuser` keyed on email, not username.

    `AbstractUser`'s inherited manager (`django.contrib.auth.models.UserManager`)
    still expects `username` as its first positional argument even after
    `username = None` below — it's never told the field is gone. Since
    `USERNAME_FIELD = "email"`, this manager (built the same way Django's own
    docs on custom user models prescribe) makes `email` that argument instead,
    which is what lets `manage.py createsuperuser` prompt for email only and
    `User.objects.create_user(email=..., password=...)` work at all.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Email/password auth; email is the login identifier."""

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
