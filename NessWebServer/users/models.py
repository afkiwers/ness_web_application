from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
# Modifies User model to make sure emails are always unique
class CustomUser(AbstractUser):
    # Make sure emails are unique
    email = models.EmailField(unique=True)
