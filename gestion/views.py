import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Producto, Venta, DetalleVenta
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

def panel_ventas(request):
    productos = Producto.objects.filter(disponible=True)
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

            nueva_venta = Venta.objects.create(metodo_pago=metodo_pago, total=0)
            total_factura = 0
            productos_procesados = 0
            
            for item in carrito_frontend:
                producto_id = item.get('id')
                cantidad = int(item.get('cantidad', 1))
                
                try:
                    producto = Producto.objects.get(id=int(producto_id))
                except (Producto.DoesNotExist, ValueError, TypeError):
                    continue 
                
                if producto.stock >= cantidad:
                    subtotal = producto.precio * cantidad
                    total_factura += subtotal
                    
                    DetalleVenta.objects.create(
                        venta=nueva_venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )
                    
                    producto.stock -= cantidad
                    producto.save()
                    productos_procesados += 1
            
            if productos_procesados > 0:
                nueva_venta.total = total_factura
                nueva_venta.save()
                messages.success(request, f"🎉 ¡Venta guardada con éxito!")
            else:
                nueva_venta.delete()
            
        except Exception:
            messages.error(request, "Hubo un problema al procesar el carrito.")
            
        return redirect('index')

    return render(request, 'gestion/index.html', {
        'productos': productos,
        'ultimas_ventas': ultimas_ventas
    })

def dashboard_ventas(request):
    ahora_local = timezone.localtime(timezone.now())
    hoy = ahora_local.date()
    
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # --- A. EVOLUCIÓN TEMPORAL DE INGRESOS ---
    ventas_diarias_query = (
        Venta.objects.annotate(periodo=TruncDate('fecha'))
        .values('periodo')
        .annotate(total_periodo=Sum('total'))
        .order_by('periodo')[:15]
    )
    dia_labels = [v['periodo'].strftime('%d %b') for v in ventas_diarias_query if v['periodo']]
    dia_valores = [float(v['total_periodo'] or 0) for v in ventas_diarias_query]

    ventas_semanales_query = (
        Venta.objects.annotate(periodo=TruncWeek('fecha'))
        .values('periodo')
        .annotate(total_periodo=Sum('total'))
        .order_by('periodo')[:12]
    )
    semana_labels = [f"Sem {v['periodo'].strftime('%W (%b)')}" for v in ventas_semanales_query if v['periodo']]
    semana_valores = [float(v['total_periodo'] or 0) for v in ventas_semanales_query]

    ventas_mensuales_query = (
        Venta.objects.annotate(periodo=TruncMonth('fecha'))
        .values('periodo')
        .annotate(total_periodo=Sum('total'))
        .order_by('periodo')
    )
    bd_mensual = {}
    for v in ventas_mensuales_query:
        if v['periodo']:
            key = v['periodo'].strftime('%Y-%m')
            bd_mensual[key] = float(v['total_periodo'] or 0)
    
    mes_labels, mes_valores = [], []
    fecha_metrica = hoy - timedelta(days=180)
    while fecha_metrica <= hoy:
        key_mes = fecha_metrica.strftime('%Y-%m')
        label_mes = fecha_metrica.strftime('%b %Y')
        if label_mes not in mes_labels:
            mes_labels.append(label_mes)
            mes_valores.append(bd_mensual.get(key_mes, 0.0))
        fecha_metrica += timedelta(days=25)

    if not dia_valores: dia_labels, dia_valores = [hoy.strftime('%d %b')], [0]
    if not semana_valores: semana_labels, semana_valores = ['Sin datos'], [0]
    if not mes_valores: mes_labels, mes_valores = ['Sin datos'], [0]

    # --- B. MIX GENERAL DE PRODUCTOS ---
    productos_mas_vendidos = (
        DetalleVenta.objects.values('producto__nombre')
        .annotate(cantidad_total=Sum('cantidad'))
        .order_by('-cantidad_total')[:5]
    )
    prod_labels = [p['producto__nombre'] for p in productos_mas_vendidos]
    prod_cantidades = [int(p['cantidad_total'] or 0) for p in productos_mas_vendidos]
    if not prod_labels: prod_labels, prod_cantidades = ['Sin ventas'], [0]

    # --- C. METRICAS PARA KPIs ---
    recaudo_dia = Venta.objects.filter(fecha__date=hoy).aggregate(total=Sum('total'))['total'] or 0
    recaudo_semana = Venta.objects.filter(fecha__date__gte=inicio_semana).aggregate(total=Sum('total'))['total'] or 0
    recaudo_mes = Venta.objects.filter(fecha__date__gte=inicio_mes).aggregate(total=Sum('total'))['total'] or 0

    top_tres_mes = (
        DetalleVenta.objects.filter(venta__fecha__date__gte=inicio_mes)
        .values('producto__nombre')
        .annotate(total_cant=Sum('cantidad'))
        .order_by('-total_cant')[:3]
    )
    lista_top_productos = []
    for i, p in enumerate(top_tres_mes, 1):
        lista_top_productos.append({
            'puesto': i,
            'nombre': p['producto__nombre'],
            'unidades': p['total_cant']
        })

    productos_bajo_stock = Producto.objects.filter(stock__lte=5).order_by('stock')
    productos_criticos = productos_bajo_stock.count()
    estado_inventario = "Alerta" if productos_criticos > 0 else "Óptimo"

    if productos_criticos > 0:
        lineas_tooltip = [f"• {p.nombre} ({p.stock} ud)" for p in productos_bajo_stock]
        tooltip_inventario = "<br>".join(lineas_tooltip)
    else:
        tooltip_inventario = "Todos los niveles de stock están estables."

    # --- D. HISTORIAL MAESTRO COMO DICCIONARIO INDEXADO ---
    ventas_db = Venta.objects.all().order_by('-id')
    total_tickets_conteo = ventas_db.count()
    
    # Lista limpia para iterar de corrido en la tabla de HTML
    historial_lista_html = []
    # Diccionario indexado por ID para JavaScript
    historial_dict_js = {}
    
    for v in ventas_db:
        fecha_local = timezone.localtime(v.fecha)
        detalles = DetalleVenta.objects.filter(venta=v).select_related('producto')
        articulos_lista = []
        for d in detalles:
            if d.producto:
                articulos_lista.append({
                    'nombre': d.producto.nombre,
                    'cantidad': d.cantidad
                })
        
        ticket_data = {
            'id': v.id,
            'fecha': fecha_local.isoformat(),
            'metodo_pago': v.metodo_pago,
            'total': float(v.total),
            'articulos': articulos_lista
        }
        
        historial_lista_html.append(ticket_data)
        historial_dict_js[str(v.id)] = ticket_data # Indexamos por ID de venta

    contexto = {
        'recaudo_dia_formateado': f"$ {recaudo_dia:,.0f}",
        'top_productos_mes': lista_top_productos,
        'mes_actual_nombre': ahora_local.strftime('%B').capitalize(),
        'recaudo_semana_formateado': f"$ {recaudo_semana:,.0f}",
        'recaudo_mes_formateado': f"$ {recaudo_mes:,.0f}",
        'estado_inventario': estado_inventario,
        'alertas_stock': productos_criticos,
        'tooltip_inventario': tooltip_inventario,
        
        'historial_tickets': historial_lista_html,
        'total_tickets_conteo': total_tickets_conteo,
        'historial_dict_json': historial_dict_js, # Enviado al tag json_script

        'data_graficos_json': json.dumps({
            'diario': {'labels': dia_labels, 'valores': dia_valores},
            'semanal': {'labels': semana_labels, 'valores': semana_valores},
            'mensual': {'labels': mes_labels, 'valores': mes_valores},
        }),
        'prod_labels': prod_labels,
        'prod_cantidades': prod_cantidades,
    }
    
    return render(request, 'gestion/dashboard.html', contexto)