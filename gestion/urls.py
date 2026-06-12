from django.urls import path
from . import views

urlpatterns = [
    # 🛒 RUTA RAÍZ: Si entras a http://127.0.0.1:8000/ te cargará el Punto de Venta (Categorías, productos, etc.)
    path('', views.panel_ventas, name='index'), 
    
    # 📊 RUTA DEL DASHBOARD: Si entras a http://127.0.0.1:8000/dashboard/ te cargará los gráficos
    path('dashboard/', views.dashboard_ventas, name='dashboard_ventas'),
]