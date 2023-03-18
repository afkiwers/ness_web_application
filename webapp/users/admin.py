from django.contrib import admin

# Register your models here.
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin

admin.site.site_header = 'CEquip Notification Handler - Administration'
admin.site.site_title = "CEquip Notification Handler - Admin Portal"
admin.site.index_title = "Administration Portal"
admin.site.login_template = 'admin/admin_login.html'


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,  # original form fieldsets, expanded
        (  # new fieldset added on to the bottom
            'Additional User Settings',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'panel_code',
                ),
            },
        ),
    )


# Register your models here.
admin.site.register(CustomUser, CustomUserAdmin)
