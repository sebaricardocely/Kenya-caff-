from django.contrib import admin
from .models import Categoria, Producto, Venta, DetalleVenta

# Configuración avanzada para ver los Productos como una tabla
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'disponible')
    list_filter = ('categoria', 'disponible')
    search_fields = ('nombre',)

# Configuración avanzada para ver las Ventas de forma organizada
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'metodo_pago', 'total')
    list_filter = ('fecha', 'metodo_pago')

# Registros simples para los modelos que no necesitan tablas complejas
admin.site.register(Categoria)
admin.site.register(DetalleVenta)