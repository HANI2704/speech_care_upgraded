from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    path('expired/', views.expired, name='expired'),
    path('activate/', views.activate, name='activate'),
]
