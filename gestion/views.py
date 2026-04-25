from django.shortcuts import render, redirect
from .models import Producto, Venta, DetalleVenta
from django.contrib import messages

def panel_ventas(request):
    # Traemos productos disponibles y las últimas 5 ventas
    productos = Producto.objects.filter(disponible=True)
    ultimas_ventas = Venta.objects.all().order_by('-fecha')[:5]
    
    if request.method == "POST":
        producto_id = request.POST.get('producto_id')
        try:
            producto = Producto.objects.get(id=producto_id)
            
            if producto.stock > 0:
                # 1. Crear la venta
                nueva_venta = Venta.objects.create(total=producto.precio, metodo_pago='EF')
                # 2. Crear el detalle
                DetalleVenta.objects.create(
                    venta=nueva_venta, 
                    producto=producto, 
                    cantidad=1, 
                    precio_unitario=producto.precio
                )
                # 3. Descontar stock
                producto.stock -= 1
                producto.save()
                
                messages.success(request, f"¡Venta de {producto.nombre} registrada!")
            else:
                messages.error(request, f"No hay stock de {producto.nombre}")
        except Producto.DoesNotExist:
            messages.error(request, "El producto no existe.")
            
        return redirect('index')

    return render(request, 'gestion/index.html', {
        'productos': productos,
        'ultimas_ventas': ultimas_ventas
    })