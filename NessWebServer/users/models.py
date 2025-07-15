from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _


# Create your models here.
# Modifies User model to make sure emails are always unique
class CustomUser(AbstractUser):
    # Make sure emails are unique
    email = models.EmailField(unique=True)

    panel_code = models.CharField("Ness Panel User Code", max_length=4, default='0000')

    enable_panic_mode = models.BooleanField(default=False)