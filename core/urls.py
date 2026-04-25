from django.contrib import admin
from django.urls import path, include # Asegúrate de que diga 'include' aquí

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')), # Esto conecta tu sistema de ventas
]