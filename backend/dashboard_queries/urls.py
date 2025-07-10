from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_queries, name='dashboard_queries'),
]
