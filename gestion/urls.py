from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_ventas, name='index'),
    path('dashboard/', views.dashboard_ventas, name='dashboard_ventas'),
]