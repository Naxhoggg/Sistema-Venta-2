from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Producto, Venta, Usuario, CierreCaja, DetalleVenta, Categoria
import json
from django.utils import timezone
from django.db.models import Sum, F
from datetime import datetime
from .forms import UsuarioRegistroForm, LoginForm
from .decorators import login_required, role_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from django.db.models import Count
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import models
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.utils import timezone
from decimal import Decimal

# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# from io import BytesIO


@login_required
def inicio(request):
    return render(request, "inventario/inicio.html")


@login_required
@role_required(["admin"])
def lista_productos(request):
    productos = Producto.objects.all()
    productos_bajos = Producto.objects.filter(
        stockActual__lte=F('stockUmbral')
    ).values('id', 'nombreProducto', 'stockActual', 'stockUmbral')
    
    categorias = Categoria.objects.all()
    context = {
        "productos": productos, 
        "categorias": categorias,
        "productos_bajos": productos_bajos
    }
    return render(request, "inventario/productos.html", context)


@login_required
@role_required(["admin", "cajero"])
def registro_venta(request):
    productos = Producto.objects.all()
    print("Productos:", productos)  # Para debug
    return render(request, "inventario/venta.html", {"productos": productos})


@login_required
@role_required(["admin", "cajero"])
def cierre_caja(request):
    if request.method == "POST":
        try:
            # Obtener las ventas del día actual
            hoy = timezone.now().date()

            # Calcular totales por m��todo de pago
            ventas_efectivo = (
                Venta.objects.filter(
                    fechaVenta__date=hoy, metodoPago="efectivo"
                ).aggregate(total=Sum("montoPagado"))["total"]
                or 0
            )

            ventas_tarjeta = (
                Venta.objects.filter(
                    fechaVenta__date=hoy, metodoPago="tarjeta"
                ).aggregate(total=Sum("montoPagado"))["total"]
                or 0
            )

            # Calcular total general
            total_ventas = ventas_efectivo + ventas_tarjeta

            # Crear registro de cierre de caja
            CierreCaja.objects.create(
                idUsuario_id=request.session.get(
                    "usuario_id"
                ),  # Usar el ID del usuario en sesión
                montoEfectivo=ventas_efectivo,
                montoTarjeta=ventas_tarjeta,
                totalVentas=total_ventas,
            )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # Para GET request, mostrar el formulario
    hoy = timezone.now().date()
    ventas_efectivo = (
        Venta.objects.filter(fechaVenta__date=hoy, metodoPago="efectivo").aggregate(
            total=Sum("montoPagado")
        )["total"]
        or 0
    )

    ventas_tarjeta = (
        Venta.objects.filter(fechaVenta__date=hoy, metodoPago="tarjeta").aggregate(
            total=Sum("montoPagado")
        )["total"]
        or 0
    )

    total_ventas = ventas_efectivo + ventas_tarjeta
    num_transacciones = Venta.objects.filter(fechaVenta__date=hoy).count()

    context = {
        "efectivo": ventas_efectivo,
        "tarjeta": ventas_tarjeta,
        "total_ventas": total_ventas,
        "num_transacciones": num_transacciones,
    }

    return render(request, "inventario/cierrecaja.html", context)


@login_required
@role_required(["admin"])
def historial_ventas(request):
    # Usar select_related para optimizar las consultas
    ventas = Venta.objects.select_related("idUsuario").prefetch_related(
        'detalleventa_set__idProducto'
    ).all().order_by("-fechaVenta")

    # Calcular ganancia para cada venta
    for venta in ventas:
        ganancia_total = 0
        detalles = venta.detalleventa_set.all()
        for detalle in detalles:
            # Calcula la ganancia por producto
            costo = detalle.idProducto.costoProducto
            precio_venta = detalle.precioUnitario
            cantidad = detalle.cantidadVendida
            ganancia_producto = (float(precio_venta) - float(costo)) * cantidad
            ganancia_total += ganancia_producto
        
        venta.ganancia = ganancia_total

    if request.session.get("rol") == "admin":
        total_ventas = sum(float(venta.montoPagado) for venta in ventas)
        ventas_mes = sum(
            float(venta.montoPagado) 
            for venta in ventas.filter(fechaVenta__month=timezone.now().month)
        )
        total_productos = DetalleVenta.objects.count()
        ganancia_total = sum(venta.ganancia for venta in ventas)

        context = {
            "ventas": ventas,
            "total_ventas": total_ventas,
            "ventas_mes": ventas_mes,
            "total_productos": total_productos,
            "ganancia_total": ganancia_total
        }
    else:
        context = {"ventas": ventas}

    return render(request, "inventario/historial.html", context)


@csrf_exempt
def finalizar_venta(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            productos = data.get("productos", [])
            metodoPago = data.get("metodoPago", "efectivo")

            # Verificar que haya productos
            if not productos:
                return JsonResponse(
                    {"success": False, "error": "No hay productos en el carrito"}
                )

            # Crear la venta
            venta = Venta.objects.create(
                idUsuario_id=request.session.get("usuario_id"),
                metodoPago=metodoPago,
                montoPagado=sum(
                    float(p["precioVenta"]) * p["cantidad"] for p in productos
                ),
            )

            # Crear detalles de venta y actualizar stock
            for producto in productos:
                prod = Producto.objects.get(id=producto["id"])

                # Verificar stock
                if prod.stockActual < producto["cantidad"]:
                    venta.delete()  # Revertir la venta si no hay stock
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"Stock insuficiente para {prod.nombreProducto}",
                        }
                    )

                DetalleVenta.objects.create(
                    idVenta=venta,
                    idProducto=prod,
                    cantidadVendida=producto["cantidad"],
                    precioUnitario=producto["precioVenta"],
                    totalProducto=producto["precioVenta"] * producto["cantidad"],
                )

                # Actualizar stock
                prod.stockActual -= producto["cantidad"]
                prod.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})


def register(request):
    if request.method == "POST":
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data["contraseña"])
            usuario.save()
            messages.success(request, "Cuenta creada exitosamente")
            return redirect("inventario:login")
    else:
        form = UsuarioRegistroForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data["rut"]
            contraseña = form.cleaned_data["contraseña"]

            try:
                # Usamos filter().first() en lugar de get() para evitar el error de múltiples objetos
                usuario = Usuario.objects.filter(rut=rut).first()
                if usuario and usuario.check_password(contraseña):
                    # Guardar datos en la sesión
                    request.session["usuario_id"] = usuario.id
                    request.session["nombre"] = (
                        f"{usuario.nombre} {usuario.apellidoPaterno}"
                    )
                    request.session["rol"] = usuario.rol
                    return redirect("inventario:inicio")
                else:
                    form.add_error(None, "RUT o contraseña incorrectos")
            except Exception as e:
                form.add_error(None, f"Error al iniciar sesión: {str(e)}")
    else:
        form = LoginForm()

    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    return redirect("inventario:login")


def redirect_to_login(request):
    if request.session.get("usuario_id"):
        return redirect("inventario:inicio")
    return redirect("inventario:login")


# @login_required
# @role_required(['admin', 'cajero'])
# def generar_informe(request):
#     ... todo el contenido de la función ...


@login_required
@role_required(["admin"])
def guardar_producto(request):
    if request.method == "POST":
        try:
            # Si se envía un ID, es una edición
            producto_id = request.POST.get("id")
            if producto_id:
                producto = Producto.objects.get(id=producto_id)
            else:
                producto = Producto()

            # Actualizar campos
            producto.nombreProducto = request.POST["nombreProducto"]
            producto.idCategoria_id = request.POST["idCategoria"]
            producto.costoProducto = float(request.POST["costoProducto"])
            producto.precioVenta = float(request.POST["precioVenta"])

            # Calcular margen de ganancia
            producto.margenGanancia = (
                (float(producto.precioVenta) - float(producto.costoProducto))
                / float(producto.costoProducto)
            ) * 100

            producto.stockActual = request.POST["stockActual"]
            producto.stockUmbral = request.POST["stockUmbral"]

            if "imagen" in request.FILES:
                producto.imagen = request.FILES["imagen"]

            producto.save()
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
@role_required(["admin"])
def eliminar_producto(request, producto_id):
    if request.method == "DELETE":
        try:
            producto = Producto.objects.get(id=producto_id)
            producto.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
@role_required(["admin"])
def guardar_categoria(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            categoria = Categoria.objects.create(
                nombreCategoria=data["nombreCategoria"]
            )
            return JsonResponse({"success": True, "categoria_id": categoria.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
@role_required(["admin"])
def generar_reporte(request):
    try:
        fecha = request.GET.get('fecha')
        is_preview = request.GET.get('preview') == 'true'
        
        # Convertir la fecha al formato correcto (DD/MM/YYYY HH:MM)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_formateada = fecha_obj.strftime('%d/%m/%Y %H:%M')
        
        # Filtrar ventas por fecha
        ventas_query = Venta.objects.filter(
            fechaVenta__date=fecha_obj.date()
        )

        # Resumen general
        total_ventas = ventas_query.count()
        total_ingresos = ventas_query.aggregate(Sum("montoPagado"))["montoPagado__sum"] or 0
        
        # Ventas por método de pago
        ventas_efectivo = ventas_query.filter(metodoPago="efectivo").aggregate(
            Sum("montoPagado"))["montoPagado__sum"] or 0
        ventas_tarjeta = ventas_query.filter(metodoPago="tarjeta").aggregate(
            Sum("montoPagado"))["montoPagado__sum"] or 0

        # Productos vendidos
        productos_vendidos = DetalleVenta.objects.filter(
            idVenta__in=ventas_query
        ).values(
            'idProducto__nombreProducto'
        ).annotate(
            cantidad=Sum('cantidadVendida'),
            total=Sum(F('precioUnitario') * F('cantidadVendida'))
        ).order_by('-cantidad')

        productos_formateados = [{
            'nombre': p['idProducto__nombreProducto'],
            'cantidad': p['cantidad'],
            'total': f"{p['total']:,.2f}"
        } for p in productos_vendidos]

        if is_preview:
            return JsonResponse({
                'fecha_reporte': fecha_formateada,
                'total_ventas': total_ventas,
                'total_ingresos': f"{total_ingresos:,.2f}",
                'ventas_efectivo': f"{ventas_efectivo:,.2f}",
                'ventas_tarjeta': f"{ventas_tarjeta:,.2f}",
                'productos_vendidos': productos_formateados
            })
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
def detalles_venta(request, venta_id):
    try:
        detalles = DetalleVenta.objects.filter(idVenta_id=venta_id).select_related('idProducto')
        
        if not detalles.exists():
            return JsonResponse({"productos": []})

        productos_venta = []
        for detalle in detalles:
            productos_venta.append({
                "nombre": detalle.idProducto.nombreProducto,
                "cantidad": detalle.cantidadVendida,
                "precio": float(detalle.precioUnitario),
                "subtotal": float(detalle.totalProducto),
                "codigo": detalle.idProducto.id
            })

        return JsonResponse({
            "productos": productos_venta,
            "success": True
        })
    except Exception as e:
        return JsonResponse({
            "error": f"Error al cargar los detalles: {str(e)}",
            "success": False
        }, status=500)

@login_required
def obtener_producto(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        data = {
            "id": producto.id,
            "nombreProducto": producto.nombreProducto,
            "idCategoria": producto.idCategoria.id,
            "costoProducto": float(producto.costoProducto),
            "precioVenta": float(producto.precioVenta),
            "stockActual": producto.stockActual,
            "stockUmbral": producto.stockUmbral,
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)


@login_required
@role_required(["admin"])
def actualizar_producto(request, producto_id):
    if request.method == "POST":
        try:
            producto = Producto.objects.get(id=producto_id)
            producto.nombreProducto = request.POST.get("nombreProducto")
            producto.idCategoria_id = request.POST.get("idCategoria")
            producto.costoProducto = request.POST.get("costoProducto")
            producto.precioVenta = request.POST.get("precioVenta")
            producto.stockActual = request.POST.get("stockActual")
            producto.stockUmbral = request.POST.get("stockUmbral")

            if "imagen" in request.FILES:
                producto.imagen = request.FILES["imagen"]

            producto.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def productos_bajo_stock(request):
    try:
        # Agregar logs para diagnóstico
        print("Consultando productos con bajo stock...")
        
        productos_bajos = Producto.objects.filter(
            stockActual__lt=5
        ).values('nombreProducto', 'stockActual')
        
        # Imprimir resultados para diagnóstico
        productos_list = list(productos_bajos)
        print(f"Productos encontrados: {len(productos_list)}")
        print("Productos:", productos_list)
        
        return JsonResponse(productos_list, safe=False)
    except Exception as e:
        print(f"Error en productos_bajo_stock: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def test_notificaciones(request):
    productos_bajos = Producto.objects.filter(
        stockActual__lte=F('stockUmbral')  # Productos con stock menor o igual al umbral
    ).values('id', 'nombreProducto', 'stockActual', 'stockUmbral')
    
    return JsonResponse(list(productos_bajos), safe=False)


@login_required
@role_required(["admin", "cajero"])
def generar_informe_cierre(request):
    # Obtener la fecha actual
    hoy = timezone.now().date()
    
    # Obtener todas las ventas del día
    ventas = Venta.objects.filter(fechaVenta__date=hoy).select_related('idUsuario')
    
    # Crear el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=1,  # Centrado
        spaceAfter=30
    )
    
    # Título
    elements.append(Paragraph(f"Informe de Cierre de Caja - {hoy.strftime('%d/%m/%Y')}", title_style))
    
    # Resumen de ventas
    ventas_efectivo = sum(v.montoPagado for v in ventas if v.metodoPago == 'efectivo')
    ventas_tarjeta = sum(v.montoPagado for v in ventas if v.metodoPago == 'tarjeta')
    total_ventas = ventas_efectivo + ventas_tarjeta
    
    resumen_data = [
        ['Resumen de Ventas'],
        ['Total Efectivo:', f'${ventas_efectivo:,.2f}'],
        ['Total Tarjeta:', f'${ventas_tarjeta:,.2f}'],
        ['Total General:', f'${total_ventas:,.2f}'],
        ['Número de Transacciones:', str(ventas.count())]
    ]
    
    t_resumen = Table(resumen_data)
    t_resumen.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 1), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
    ]))
    
    elements.append(t_resumen)
    elements.append(Spacer(1, 20))
    
    # Detalle de ventas
    if ventas:
        detalle_data = [['ID', 'Hora', 'Método', 'Cajero', 'Monto']]
        for venta in ventas:
            detalle_data.append([
                str(venta.id),
                venta.fechaVenta.strftime('%H:%M'),
                venta.metodoPago.title(),
                f"{venta.idUsuario.nombre} {venta.idUsuario.apellidoPaterno}",
                f"${venta.montoPagado:,.2f}"
            ])
        
        t_detalle = Table(detalle_data)
        t_detalle.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
        ]))
        
        elements.append(Paragraph("Detalle de Ventas", title_style))
        elements.append(t_detalle)
    
    # Generar PDF
    doc.build(elements)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=informe_cierre_caja.pdf'
    
    return response
