from django.urls import path
from ness_comms import views

urlpatterns = [
    path('', views.home, name='home'),
    path('history/', views.history, name='alarm-history'),
    path('settings/', views.zone_settings, name='zone-settings'),
    path('settings/zones/<int:zone_id>/rename/', views.zone_rename, name='zone-rename'),
]
