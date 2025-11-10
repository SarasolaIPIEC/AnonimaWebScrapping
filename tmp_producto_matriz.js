/**
 * Manejo de productos matriz - Redirección automática y lógica de precios
 */

const API_UNIFICADA_BASE = (() => {
    if (typeof window === 'undefined') return '';

    const base = typeof window.URL_API_UNIFICADA === 'string'
        ? window.URL_API_UNIFICADA.trim()
        : '';

    if (base) {
        return base.replace(/\/+$/, '');
    }

    const meta = document.querySelector('meta[name="api-unificada-base"]');
    if (meta && typeof meta.content === 'string' && meta.content.trim() !== '') {
        return meta.content.trim().replace(/\/+$/, '');
    }

    return '';
})();

class ProductoMatrizHandler {
    constructor() {
        this.init();
    }

    init() {
        // Verificar si estamos en una página de producto
        if (this.isProductPage()) {
            this.checkAndRedirect();
        }
    }

    /**
     * Verifica si estamos en una página de producto
     */
    isProductPage() {
        return window.location.pathname.includes('/art_');
    }

    /**
     * Obtiene el código del producto de la URL
     */
    getProductCode() {
        const path = window.location.pathname;
        const match = path.match(/\/art_([^\/]+)/);
        return match ? match[1] : null;
    }

    /**
     * Verifica si es un producto padre y redirecciona si es necesario
     */
    async checkAndRedirect() {
    	return true;
        const codigo = this.getProductCode();
        if (!codigo) return;

        try {
            // Verificar si es un producto padre usando el endpoint del backend
            const primerHijo = await this.obtenerPrimerHijoConStock(codigo);

            if (primerHijo) {
                // Es un producto padre, redireccionar al primer hijo con stock
                console.log(`Redirigiendo de producto padre ${codigo} a hijo ${primerHijo}`);
                window.location.replace(`/art_${primerHijo}`);
                return;
            }

            // No es un producto padre o no hay hijos con stock

            // Verificar si es un producto padre para mostrar mensaje apropiado
            const esPadreMatriz = await this.verificarSiEsPadreMatriz(codigo);
            if (esPadreMatriz) {
                console.log(`Producto padre ${codigo} sin hijos con stock`);
                this.mostrarMensajeSinStock();
            } else {
                console.log(`Producto ${codigo} no es padre de matriz, cargando normalmente`);
            }

        } catch (error) {
            console.error('Error verificando producto matriz:', error);

            // En caso de error, intentar cargar normalmente
            console.log('Error en verificación de matriz, cargando producto normalmente');
        }
    }

    /**
     * Verifica si un producto es padre de matriz
     */
    async verificarSiEsPadreMatriz(codigo) {
        try {
            // Intentar obtener datos del producto desde el backend unificado
            const endpoint = API_UNIFICADA_BASE
                ? `${API_UNIFICADA_BASE}/catalogo/articulo/${codigo}`
                : `/catalogo/articulo/${codigo}`;

            const response = await fetch(endpoint, {
                credentials: API_UNIFICADA_BASE ? 'include' : 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                const esPadreMatriz = data.esPadreMatriz === true;
                console.log(`Verificación de producto ${codigo}: esPadreMatriz = ${esPadreMatriz}`);
                return esPadreMatriz;
            } else if (response.status === 404) {
                console.log(`Producto ${codigo} no encontrado`);
                return false;
            } else {
                console.error(`Error ${response.status} verificando producto ${codigo}`);
                return false;
            }
        } catch (error) {
            console.error('Error verificando si es padre matriz:', error);
            return false;
        }
    }

    /**
     * Obtiene el primer hijo con stock de un producto padre
     */
    async obtenerPrimerHijoConStock(codigoPadre) {
        try {
            const response = await fetch(window.URL_API_UNIFICADA + `/catalogo/primer-hijo-stock/${codigoPadre}`);

            if (response.ok) {
                const data = await response.json();
                return data.codigoHijo;
            } else if (response.status === 404) {
                // No hay hijos con stock
                console.log(`No hay hijos con stock para producto padre ${codigoPadre}`);
                return null;
            } else {
                console.error(`Error ${response.status} obteniendo primer hijo con stock`);
                return null;
            }

        } catch (error) {
            console.error('Error obteniendo primer hijo con stock:', error);
            return null;
        }
    }

    /**
     * Muestra indicador de carga durante la verificación
     */
    mostrarIndicadorCarga() {
        const loader = document.createElement('div');
        loader.className = 'cargando-redireccion';
        loader.innerHTML = `
            <div class="spinner"></div>
            <div style="margin-top: 10px; color: #666;">Verificando producto...</div>
        `;
        document.body.appendChild(loader);
    }

    /**
     * Oculta el indicador de carga
     */
    ocultarIndicadorCarga() {
        const loader = document.querySelector('.cargando-redireccion');
        if (loader) {
            loader.remove();
        }
    }

    /**
     * Muestra mensaje cuando no hay stock disponible
     */
    mostrarMensajeSinStock() {
    	return true;
        const mensaje = document.createElement('div');
        mensaje.className = 'mensaje-sin-stock';
        mensaje.innerHTML = `
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center;">
                <strong>Producto no disponible</strong><br>
                Este producto tiene múltiples variantes pero ninguna está disponible actualmente.
            </div>
        `;

        // Insertar al inicio del contenido principal
        const contenido = document.querySelector('.contenido-principal') || document.body;
        contenido.insertBefore(mensaje, contenido.firstChild);
    }

    /**
     * Formatea precio para mostrar en rangos
     */
    static formatearPrecio(precio) {
        return precio ? precio.toFixed(2) : '0.00';
    }

    /**
     * Genera texto de precio para productos matriz
     */
    static generarTextoPrecio(producto) {
        if (producto.esPadreMatriz && producto.precioDesde && producto.precioHasta) {
            if (producto.precioDesde === producto.precioHasta) {
                return `$${this.formatearPrecio(producto.precioDesde)}`;
            } else {
                return `Desde $${this.formatearPrecio(producto.precioDesde)} hasta $${this.formatearPrecio(producto.precioHasta)}`;
            }
        } else {
            return `$${this.formatearPrecio(producto.precioMostrar)}`;
        }
    }

    /**
     * Actualiza precios en listados de productos
     */
    static actualizarPreciosEnListados() {
        // Buscar todas las tarjetas de producto
        const tarjetas = document.querySelectorAll('.card');

        tarjetas.forEach(tarjeta => {
            const linkElement = tarjeta.closest('a');
            if (!linkElement) return;

            const precioElement = tarjeta.querySelector('.precio span');
            if (!precioElement) return;

            // Obtener datos del producto desde atributos data
            const esPadreMatriz = linkElement.dataset.esPadreMatriz === 'true';
            const precioDesde = parseFloat(linkElement.dataset.precioDesde);
            const precioHasta = parseFloat(linkElement.dataset.precioHasta);

            if (esPadreMatriz && precioDesde && precioHasta) {
                if (precioDesde === precioHasta) {
                    precioElement.textContent = `$${precioDesde.toFixed(2)}`;
                    precioElement.className = 'precio-unico';
                } else {
                    precioElement.textContent = `Desde $${precioDesde.toFixed(2)} hasta $${precioHasta.toFixed(2)}`;
                    precioElement.className = 'precio-rango';
                }
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new ProductoMatrizHandler();

    // Actualizar precios en listados si estamos en una página de listado
    if (window.location.pathname.includes('/categoria/') || window.location.pathname.includes('/buscar/')) {
        ProductoMatrizHandler.actualizarPreciosEnListados();
    }
});

// Exportar para uso en otros archivos
window.ProductoMatrizHandler = ProductoMatrizHandler; 
