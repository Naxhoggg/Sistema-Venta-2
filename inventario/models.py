from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Categoria(models.Model):
    nombreCategoria = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return str(self.nombreCategoria)


class Producto(models.Model):
    idCategoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombreProducto = models.CharField(max_length=25)
    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)
    costoProducto = models.DecimalField(max_digits=10, decimal_places=2)
    precioVenta = models.DecimalField(max_digits=10, decimal_places=2)
    margenGanancia = models.DecimalField(max_digits=10, decimal_places=2)
    stockActual = models.IntegerField()
    stockUmbral = models.IntegerField()
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.nombreProducto)


class Usuario(models.Model):
    ROLES = [
        ("admin", "Administrador"),
        ("cajero", "Cajero"),
    ]
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=25)
    apellidoPaterno = models.CharField(max_length=25)
    apellidoMaterno = models.CharField(max_length=25)
    contraseña = models.CharField(max_length=40)
    rol = models.CharField(max_length=25, choices=ROLES)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.contraseña = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contraseña)


class Venta(models.Model):
    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
    ]
    idUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    metodoPago = models.CharField(max_length=10, choices=METODOS_PAGO)
    montoPagado = models.DecimalField(max_digits=10, decimal_places=2)
    fechaVenta = models.DateTimeField(auto_now_add=True)


class DetalleVenta(models.Model):
    idVenta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    idProducto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidadVendida = models.IntegerField()
    precioUnitario = models.DecimalField(max_digits=6, decimal_places=2)
    totalProducto = models.DecimalField(max_digits=8, decimal_places=2)


class CierreCaja(models.Model):
    idUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    montoEfectivo = models.DecimalField(max_digits=10, decimal_places=2)
    montoTarjeta = models.DecimalField(max_digits=10, decimal_places=2)
    totalVentas = models.DecimalField(max_digits=10, decimal_places=2)
    fechaCierre = models.DateTimeField(auto_now_add=True)


class Oferta(models.Model):
    idProducto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    descuentoPorcentaje = models.DecimalField(max_digits=10, decimal_places=2)
    fechaInicio = models.DateTimeField()
    fechaFin = models.DateTimeField()
