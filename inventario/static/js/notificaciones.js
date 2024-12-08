function mostrarMensajeNotificacion(mensaje, tipo) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px; box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);';
    
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${mensaje}
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

function actualizarNotificaciones() {
    fetch("/inventario/test-notificaciones")
        .then(response => response.json())
        .then(productos => {
            const contador = document.getElementById("notificacionesContador");
            const lista = document.getElementById("notificacionesLista");
            
            if (!contador || !lista) return;
            
            // Actualizar contador y badge
            contador.textContent = productos.length;
            contador.style.display = productos.length > 0 ? "inline" : "none";
            
            // Limpiar y actualizar lista
            lista.innerHTML = "";
            
            if (productos.length === 0) {
                lista.innerHTML = '<div class="dropdown-item text-muted">No hay productos con stock bajo</div>';
                return;
            }
            
            // Agregar productos al dropdown
            productos.forEach(producto => {
                const item = document.createElement("div");
                item.className = "dropdown-item border-bottom py-2";
                item.innerHTML = `
                    <div class="d-flex align-items-center text-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <div>
                            <strong>${producto.nombreProducto}</strong>
                            <br>
                            <small>Stock actual: ${producto.stockActual} (Umbral: ${producto.stockUmbral})</small>
                        </div>
                    </div>
                `;
                lista.appendChild(item);
            });
        });
}

// Inicializar notificaciones cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    actualizarNotificaciones();
    // Verificar cada 30 segundos
    setInterval(actualizarNotificaciones, 30000);
});