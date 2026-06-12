from django.contrib import admin  # <-- Revisa que esta línea esté idéntica
from .models import Categoria, Producto, Venta, DetalleVenta

# Configuraciones avanzadas para que el panel sea ultra cómodo y profesional:

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Esto creará columnas organizadas para ver el stock, precio y código de un vistazo
    list_display = ('codigo', 'nombre', 'categoria', 'precio', 'stock', 'disponible')
    list_editable = ('precio', 'stock', 'disponible') # Te permite editar stock sin entrar al producto
    search_fields = ('nombre', 'codigo')
    list_filter = ('categoria', 'disponible')

# Configuramos la venta junto con sus detalles en la misma pantalla (Inline)
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0 # No mostrar filas vacías innecesarias
    readonly_fields = ('producto', 'cantidad', 'precio_unitario')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'metodo_pago', 'total')
    list_filter = ('metodo_pago', 'fecha')
    inlines = [DetalleVentaInline] # Muestra qué compraron dentro de la misma venta