document.getElementById('nuevoProductoForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const producto = {
        nombreProducto: document.getElementById('nombre').value,
        nombreCategoria: document.getElementById('categoria').options[document.getElementById('categoria').selectedIndex].text,
        costoProducto: parseFloat(document.getElementById('costoProducto').value),
        precioVenta: parseFloat(document.getElementById('precio').value),
        stockActual: parseInt(document.getElementById('stock').value),
        stockUmbral: parseInt(document.getElementById('umbral').value),
        imagen_url: document.getElementById('imagen_url').value,
        fechaCreacion: new Date()
    };

    fetch('/inventario/admin/nuevo-producto/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(producto)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Producto agregado correctamente');
            window.location.reload();
        } else {
            alert(data.error || 'Error al agregar el producto');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al agregar el producto');
    });
});

// Función para obtener el CSRF token (igual que en venta.html)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function editarProducto(id) {
    console.log('Editando producto con ID:', id);
    fetch(`/inventario/admin/producto/${id}/`, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(producto => {
        // Llenar el modal con los datos
        document.getElementById('editNombre').value = producto.nombreProducto;
        document.getElementById('editCosto').value = producto.costoProducto;
        document.getElementById('editPrecio').value = producto.precioVenta;
        document.getElementById('editStock').value = producto.stockActual;
        document.getElementById('editUmbral').value = producto.stockUmbral;
        document.getElementById('editProductoId').value = id;
        
        // Mostrar el modal
        const modal = new bootstrap.Modal(document.getElementById('editarProductoModal'));
        modal.show();
    })
    .catch(error => {
        console.error('Error al cargar el producto:', error);
        alert('Error al cargar los datos del producto');
    });
}

// Agregar el manejador del formulario de edición
document.getElementById('editarProductoForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const id = document.getElementById('editProductoId').value;
    
    const data = {
        nombreProducto: document.getElementById('editNombre').value,
        costoProducto: document.getElementById('editCosto').value,
        precioVenta: document.getElementById('editPrecio').value,
        stockActual: document.getElementById('editStock').value,
        stockUmbral: document.getElementById('editUmbral').value
    };

    fetch(`/inventario/admin/producto/${id}/actualizar/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || 'Error al actualizar el producto');
        }
    });
});
