from django.contrib import admin

# Register your models here.
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin

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
