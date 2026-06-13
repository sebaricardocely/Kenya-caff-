from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')), # Incluye las rutas de la app directamente en la raíz
]

# =====================================================================
# PERSONALIZACIÓN DE LA MARCA EN EL PANEL DE ADMINISTRACIÓN
# =====================================================================

# Reemplaza "Administración de Django" en la barra superior azul
admin.site.site_header = "Admin Kenya"

# Reemplaza "Sitio administrativo" en el cuerpo central de la página
admin.site.index_title = "Panel de Gestión Kenya Caffé"

# Reemplaza el texto en la pestaña de tu navegador de internet
admin.site.site_title = "Admin Kenya"