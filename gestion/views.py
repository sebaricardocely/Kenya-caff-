import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import ExtractWeekDay
from django.utils import timezone
from datetime import timedelta
from .models import Producto, Venta, DetalleVenta

# ==========================================================
# 1. PANEL DE VENTAS PRINCIPAL (PUNTO DE VENTA)
# ==========================================================
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


# ==========================================================
# 2. VISTA DEL DASHBOARD (PROCESAMIENTO ANALÍTICO REAL)
# ==========================================================
def dashboard_ventas(request):
    hoy = timezone.now().date()
    hace_una_semana = hoy - timedelta(days=6)

    # ----------------------------------------------------------
    # A. INGRESOS REALES POR DÍA DE LA SEMANA (Mapeo Cronológico)
    # ----------------------------------------------------------
    # ExtractWeekDay extrae el día: 1=Domingo, 2=Lunes, 3=Martes... 7=Sábado
    ventas_por_dia = (
        Venta.objects.filter(fecha__date__range=[hace_una_semana, hoy])
        .annotate(dia_semana=ExtractWeekDay('fecha'))
        .values('dia_semana')
        .annotate(total_dia=Sum('total'))
        .order_by('dia_semana')
    )
    
    # Mapeo estándar para organizar los gráficos de Lunes a Domingo de manera natural
    dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    valores_dias = [0] * 7  # Inicializamos la semana con $0 para cada día
    
    for registro in ventas_por_dia:
        num_django = registro['dia_semana']
        total = float(registro['total_dia'] or 0)
        
        if num_django == 1:  # En Django, 1 es Domingo (Última posición del arreglo)
            valores_dias[6] = total
        else:  # Lunes (2) a Sábado (7) se mapean restando 2 al índice del arreglo
            valores_dias[num_django - 2] = total

    # ----------------------------------------------------------
    # B. TOP 5 PRODUCTOS MÁS VENDIDOS (Desde DetalleVenta)
    # ----------------------------------------------------------
    productos_mas_vendidos = (
        DetalleVenta.objects.filter(venta__fecha__date__range=[hace_una_semana, hoy])
        .values('producto__nombre')
        .annotate(cantidad_total=Sum('cantidad'))
        .order_by('-cantidad_total')[:5]
    )
    
    prod_labels = [p['producto__nombre'] for p in productos_mas_vendidos]
    prod_cantidades = [int(p['cantidad_total'] or 0) for p in productos_mas_vendidos]

    # Respaldo visual en caso de que no existan transacciones aún
    if not prod_labels:
        prod_labels = ['Sin ventas']
        prod_cantidades = [0]

    # ----------------------------------------------------------
    # C. CÁLCULO DE INDICADORES REALES (KPIs PARA TARJETAS)
    # ----------------------------------------------------------
    # 1. Ventas de Hoy (Filtro por fecha actual)
    ventas_hoy_query = Venta.objects.filter(fecha__date=hoy).aggregate(total=Sum('total'))
    ventas_hoy = ventas_hoy_query['total'] if ventas_hoy_query['total'] else 0

    # 2. Facturación Semanal (Suma acumulada real de los últimos 7 días)
    ventas_semanal = sum(valores_dias)

    # 3. Estado de Inventario (Alerta si hay algún producto con stock crítico <= 5 unidades)
    productos_criticos = Producto.objects.filter(stock__lte=5).count()
    estado_inventario = "Alerta" if productos_criticos > 0 else "Óptimo"

    # 4. Datos del Producto Líder para los textos informativos
    producto_lider = prod_labels[0] if productos_mas_vendidos else "Ninguno"
    unidades_lider = prod_cantidades[0] if productos_mas_vendidos else 0

    # ----------------------------------------------------------
    # D. ESTRUCTURACIÓN DEL CONTEXTO UNIFICADO
    # ----------------------------------------------------------
    contexto = {
        # Strings listos y formateados para las tarjetas superiores
        'ventas_hoy_formateado': f"$ {ventas_hoy:,.0f}",
        'ventas_semanal_formateado': f"$ {ventas_semanal:,.0f}" if ventas_semanal < 1000000 else f"$ {ventas_semanal/1000000:.2f}M",
        'producto_top_kpi': f"{unidades_lider} Unidades",
        'producto_top_subtexto': f"{producto_lider} lidera",
        'estado_inventario': estado_inventario,
        'alertas_stock': productos_criticos,

        # Datos nativos serializados para los scripts de Chart.js
        'dias_labels': dias_nombre,
        'dias_totales': valores_dias,
        'prod_labels': prod_labels,
        'prod_cantidades': prod_cantidades,
    }
    
    return render(request, 'gestion/dashboard.html', contexto)