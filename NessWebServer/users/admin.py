from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django.shortcuts import redirect
from django.urls import reverse

# Register your models here.
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin


class TwoFactorAdminSite(OTPAdminSite):
    """Admin site that redirects unauthenticated users to the 2FA login page."""

    def login(self, request, extra_context=None):
        if not request.user.is_authenticated:
            next_url = request.get_full_path()
            return redirect(f"{reverse('two_factor:login')}?next={next_url}")
        if not request.user.is_verified():
            # Authenticated but no 2FA device set up — send to setup page
            return redirect(reverse('two_factor:setup'))
        return super().login(request, extra_context)


# Require 2FA to access the admin site
admin.site.__class__ = TwoFactorAdminSite

admin.site.site_header = 'Ness D8x/D16x Alarm Control Panel - Administration'
admin.site.site_title = "Ness D8x/D16x Alarm Control Panel - Admin Portal"
admin.site.index_title = "Administration Portal"
admin.site.login_template = 'admin/admin_login.html'


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Additional User Settings", {
            "fields": ("panel_code", "enable_panic_mode"),
        }),
    )

# Register your models here.
admin.site.register(CustomUser, CustomUserAdmin)
