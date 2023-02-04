from django.contrib import admin

# Register your models here.
from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin


admin.site.site_header = 'CEquip Notification Handler - Administration'
admin.site.site_title = "CEquip Notification Handler - Admin Portal"
admin.site.index_title = "Administration Portal"
admin.site.login_template = 'admin/admin_login.html'


# Register your models here.
admin.site.register(CustomUser, UserAdmin)