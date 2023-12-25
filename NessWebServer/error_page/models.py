from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

import logging

_LOGGER = logging.getLogger(__name__)


class Error(models.Model):
    function_name = models.CharField("Function", max_length=150)

    description = models.TextField("Description")

    code_line = models.IntegerField("Code Line")

    file_name = models.CharField("Function", max_length=150)

    class Meta:
        verbose_name = "Error"
        verbose_name_plural = "Error"

    def __str__(self):
        return self.function_name

    def get_absolute_url(self):
        return reverse("Error_details", kwargs={"pk": self.pk})