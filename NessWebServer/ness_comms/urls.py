from django.urls import path

from ness_comms import views

urlpatterns = [
    path('', views.home, name='home'),
    path('connectivity/', views.connectivity, name='connectivity'),
]
