from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.redirect_to_login, name="redirect_to_login"),
    path("inicio/", views.inicio, name="inicio"),
    path("register/", views.register, name="register"),
    path("productos/", views.lista_productos, name="lista_productos"),
    path("ventas/", views.registro_venta, name="registro_venta"),
    path("historial/", views.historial_ventas, name="historial_ventas"),
    path("cierre-caja/", views.cierre_caja, name="cierre_caja"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # path("generar-informe/", views.generar_informe, name="generar_informe"),
    path("finalizar-venta/", views.finalizar_venta, name="finalizar_venta"),
    path('producto/guardar/', views.guardar_producto, name='guardar_producto'),
    path('producto/<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('categoria/guardar/', views.guardar_categoria, name='guardar_categoria'),
    path('generar-reporte/', views.generar_reporte, name='generar_reporte'),
    path('producto/<int:producto_id>/', views.obtener_producto, name='obtener_producto'),
    path('producto/<int:producto_id>/actualizar/', views.actualizar_producto, name='actualizar_producto'),
    path('venta/<int:venta_id>/detalles/', views.detalles_venta, name='detalles_venta'),
    path('productos-bajo-stock', views.productos_bajo_stock, name='productos_bajo_stock'),
    path('test-notificaciones', views.test_notificaciones, name='test_notificaciones'),
    path('generar-informe-cierre/', views.generar_informe_cierre, name='generar_informe_cierre'),
]
