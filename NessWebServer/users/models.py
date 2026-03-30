from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _


class DeviceToken(models.Model):
    """FCM device token for push notifications (one per device per user)."""
    user = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, related_name='device_tokens'
    )
    fcm_token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    notify_on_armed = models.BooleanField(default=True)
    notify_on_siren = models.BooleanField(default=True)
    notify_on_panic = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'fcm_token')


# Create your models here.
# Modifies User model to make sure emails are always unique
class CustomUser(AbstractUser):
    # Make sure emails are unique
    email = models.EmailField(unique=True)

    panel_code = models.CharField("Ness Panel User Code", max_length=4, default='0000')

    enable_panic_mode = models.BooleanField(default=False)

    shortcut_token = models.CharField(
        "Siri Shortcut Token",
        max_length=64,
        null=True,
        blank=True,
        default=None,
        unique=True,
        help_text="Long-lived token for Siri Shortcuts. Regenerate to revoke access.",
    )