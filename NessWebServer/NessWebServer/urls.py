"""NessWebServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.authtoken import views as rest_views

from NessWebServer import settings
from NessWebServer.api.router import api_logout, main_router

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('ness_comms.urls')),
    path('', include('users.urls')),

    path('api/', include(main_router.urls)),
    path('api/api-token-auth/', rest_views.obtain_auth_token, name='api-token-auth'),
    path('api/logout/', api_logout, name='api-logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'error_page.views.handler404'
handler500 = 'error_page.views.handler500'
