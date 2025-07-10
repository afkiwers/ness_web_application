from django.contrib import admin

from error_page.models import Error


class ErrorDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Error._meta.fields]


admin.site.register(Error, ErrorDisplay)
