from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Categorías"

class Producto(models.Model):
    # NUEVO CAMPO: Único para cada producto (ideal para SKUs o códigos de barras)
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Código/SKU", 
        null=True, 
        blank=True
    )
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        # Actualizamos el str para que también muestre el código si existe
        return f"[{self.codigo}] {self.nombre} - ${self.precio}" if self.codigo else f"{self.nombre} - ${self.precio}"

class Venta(models.Model):
    # ACTUALIZADO: Añadimos la opción 'QR' para los pagos con código escaneable
    METODOS_PAGO = [
        ('EF', 'Efectivo'),
        ('QR', 'Código QR (Nequi/Daviplata/Bancolombia)'),
        ('TR', 'Transferencia Directa'),
        ('TD', 'Tarjeta'),
    ]
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=2, choices=METODOS_PAGO, default='EF')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"