from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        verbose_name=_('username'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique':  _("A user with that username already exists."),
            },
        )

    email = models.EmailField(
        verbose_name=_('email address'),
        unique=True,
        )

    def __json__(self):
        # to enable serialization by `Celery`
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
        }
