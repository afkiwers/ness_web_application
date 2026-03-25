from django.urls import path
from ness_comms import views

urlpatterns = [
    path('', views.home, name='home'),
    path('history/', views.history, name='alarm-history'),
    path('settings/', views.zone_settings, name='zone-settings'),
    path('settings/zones/<int:zone_id>/rename/', views.zone_rename, name='zone-rename'),
    path('statistics/', views.statistics, name='statistics'),
    path('statistics/data/', views.statistics_data, name='statistics-data'),
    path('statistics/export/', views.statistics_export, name='statistics-export'),
    path('history/export/', views.history_export, name='history-export'),
    path('zones/<int:zone_id>/history/', views.zone_history_data, name='zone-history-data'),
    path('settings/ota/toggle/', views.toggle_ota, name='toggle-ota'),
    path('health/', views.health_check, name='health-check'),
    path('shortcuts/disarm/', views.shortcut_disarm, name='shortcut-disarm'),
]
