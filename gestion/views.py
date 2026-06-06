import json
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Producto, Venta, DetalleVenta

# 1. PANEL DE VENTAS PRINCIPAL (PUNTO DE VENTA)
def panel_ventas(request):
    # Traemos productos disponibles
    productos = Producto.objects.filter(disponible=True)
    # Ordenamos por id descendente para ver las últimas transacciones arriba
    ultimas_ventas = Venta.objects.all().order_by('-id')[:5]
    
    if request.method == "POST":
        items_json = request.POST.get('items_pedido')
        metodo_pago = request.POST.get('metodo_pago', 'EF') 
        
        if not items_json:
            messages.error(request, "El carrito de compras está vacío.")
            return redirect('index')
            
        try:
            carrito_frontend = json.loads(items_json)
            
            if not carrito_frontend or len(carrito_frontend) == 0:
                messages.error(request, "No seleccionaste ningún producto.")
                return redirect('index')

            # Creamos la cabecera de la venta inicialmente en 0
            nueva_venta = Venta.objects.create(
                metodo_pago=metodo_pago,
                total=0
            )
            
            total_factura = 0
            productos_procesados = 0
            
            for item in carrito_frontend:
                producto_id = item.get('id')
                cantidad = int(item.get('cantidad', 1))
                
                try:
                    producto = Producto.objects.get(id=int(producto_id))
                except (Producto.DoesNotExist, ValueError, TypeError):
                    # Si un ID específico falla, avisa cuál es pero permite procesar el resto
                    messages.error(request, f"El producto con ID {producto_id} no existe en la base de datos.")
                    continue 
                
                # Verificar stock antes de descontar
                if producto.stock >= cantidad:
                    subtotal = producto.precio * cantidad
                    total_factura += subtotal
                    
                    # Registramos el detalle de la venta
                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )
                    
                    # Descontamos existencias del inventario
                    producto.stock -= cantidad
                    producto.save()
                    productos_procesados += 1
                else:
                    messages.error(request, f"¡Alerta! No hay stock suficiente de {producto.nombre} (Disponibles: {producto.stock}).")
            
            # Si se logró procesar al menos un artículo válido del carrito
            if productos_procesados > 0:
                nueva_venta.total = total_factura
                nueva_venta.save()
                messages.success(request, f"🎉 ¡Venta #{nueva_venta.id} guardada con éxito por ${total_factura:,.0f}!")
            else:
                # Si ningún producto tenía stock o era válido, eliminamos la cabecera vacía
                nueva_venta.delete()
                messages.error(request, "No se pudo procesar la venta porque ningún artículo cumple con los requisitos.")
            
        except json.JSONDecodeError:
            messages.error(request, "Hubo un problema al procesar los datos del carrito.")
        except Exception as e:
            messages.error(request, f"Error inesperado: {str(e)}")
            
        return redirect('index')

    return render(request, 'gestion/index.html', {
        'productos': productos,
        'ultimas_ventas': ultimas_ventas
    })


# 2. VISTA DEL DASHBOARD (Para solucionar la pantalla en blanco)
def dashboard_ventas(request):
    # Datos de prueba estructurados para alimentar directamente tus gráficos en el HTML
    contexto = {
        'dias_labels': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
        'dias_totales': [120000, 150000, 90000, 210000, 180000, 320000, 0],
        'prod_labels': ['Capuchino', 'Tinto y Espresso', 'Sandwich especial', 'Sandwich Kenya'],
        'prod_cantidades': [45, 60, 22, 18],
        'meses_labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        'meses_totales': [1400000, 1650000, 1200000, 1900000, 2100000, 2500000],
    }
    return render(request, 'gestion/dashboard.html', contexto)