from django.shortcuts import redirect
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            return redirect('inventario:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.session.get('usuario_id'):
                return redirect('inventario:login')
            if request.session.get('rol') not in allowed_roles:
                return redirect('inventario:inicio')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator