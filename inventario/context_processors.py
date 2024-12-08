from django.db.models import F
from .models import Producto

def productos_bajos_context(request):
    """
    Este context processor agrega la variable productos_bajos
    a todas las plantillas automáticamente
    """
    if request.session.get('rol') == 'admin':
        productos_bajos = Producto.objects.filter(
            stockActual__lte=F('stockUmbral')
        ).values('id', 'nombreProducto', 'stockActual', 'stockUmbral')
        return {'productos_bajos': productos_bajos}
    return {'productos_bajos': []}