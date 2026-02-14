from django.urls import path
from . import views



# This is the URL configuration for the "monitor" app.
#  It defines the URL patterns for the app and maps them to the corresponding view functions in views.py.

urlpatterns = [
    path("", views.index, name="index"),
    path("api/latest", views.api_latest, name="api_latest"),
    path("api/data", views.api_data, name="api_data"),
]
