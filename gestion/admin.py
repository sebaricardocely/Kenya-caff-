# admin.py
from django.contrib import admin
from .models import Categoria, Producto, Venta, DetalleVenta

class KenyaAdminBase(admin.ModelAdmin):
    class Media:
        # Probemos con la ruta absoluta desde el servidor
        css = {
            'all': ('static/css/admin_custom.css',) 
        }

# ¡IMPORTANTE!: Todos deben heredar de KenyaAdminBase
@admin.register(Producto)
class ProductoAdmin(KenyaAdminBase): 
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'disponible')

@admin.register(Venta)
class VentaAdmin(KenyaAdminBase):
    list_display = ('id', 'fecha', 'metodo_pago', 'total')

# Si usas admin.site.register, cámbialos para que usen la base:
@admin.register(Categoria)
class CategoriaAdmin(KenyaAdminBase):
    pass

@admin.register(DetalleVenta)
class DetalleVentaAdmin(KenyaAdminBase):
    pass