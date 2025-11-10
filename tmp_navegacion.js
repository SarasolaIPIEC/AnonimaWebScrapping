function obtenerCookieLocal(nombre) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${nombre}=`);
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
    return null;
}

function getBaseDomainLocal() {
    if (typeof baseDomain !== 'undefined') {
        return baseDomain;
    }

    const hostname = window.location.hostname;
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (ipRegex.test(hostname)) {
        return '';
    }

    const parts = hostname.split('.');
    if (parts.length === 1) {
        return `.${hostname}`;
    }

    if (parts.length > 2) {
        return `.${parts.slice(-2).join('.')}`;
    }

    return `.${hostname}`;
}

function escribirCookie(nombre, valor, dominio, fechaExpiracion) {
    if (!nombre) {
        return;
    }
    let cookie = `${nombre}=${valor ?? ''}; path=/;`;
    if (fechaExpiracion) {
        cookie += ` expires=${fechaExpiracion.toUTCString()};`;
    }
    if (dominio) {
        cookie += ` domain=${dominio};`;
    }
    document.cookie = cookie;
}

function borrarCookie(nombre, dominio) {
    if (!nombre) {
        return;
    }
    let cookie = `${nombre}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;`;
    if (dominio) {
        cookie += ` domain=${dominio};`;
    }
    document.cookie = cookie;
}

function aplicarCodigoPostalDesdeQuery() {
    const params = new URLSearchParams(window.location.search);
    const cpParam = (params.get('cp') || params.get('codigoPostal') || '').trim();

    if (!cpParam) {
        return;
    }

    const cpEnCookies = obtenerCookieLocal('codigoPostal');
    if (cpEnCookies && cpEnCookies === cpParam) {
        params.delete('cp');
        params.delete('codigoPostal');
        const nuevaUrl = `${window.location.pathname}${params.toString() ? `?${params}` : ''}${window.location.hash}`;
        window.history.replaceState({}, '', nuevaUrl);
        return;
    }

    if (window.__aplicandoCpDesdeQuery === cpParam) {
        return;
    }
    window.__aplicandoCpDesdeQuery = cpParam;

    const fechaExpiracion = new Date();
    fechaExpiracion.setFullYear(fechaExpiracion.getFullYear() + 1);
    const dominio = getBaseDomainLocal();
    const endpointBase = typeof DOMINIO_WEB !== 'undefined' && DOMINIO_WEB ? DOMINIO_WEB : window.location.origin;
    const recurso = `${endpointBase.replace(/\/$/, '')}/sucursal/${encodeURIComponent(cpParam)}`;

    fetch(recurso, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(respuesta => {
            if (!respuesta.ok) {
                throw new Error(`Error ${respuesta.status}`);
            }
            return respuesta.json();
        })
        .then(data => {
            let cambios = false;

            if (data && data.electro && data.electro.existeSucursal) {
                escribirCookie('Id-Sucursal-Electro', data.electro.idSucursalVirtualTecno, dominio, fechaExpiracion);
                escribirCookie('descripcionLocalidadCabezal', data.electro.descripcionLocalidadCabezal, dominio, fechaExpiracion);
                escribirCookie('tipoEnvio', data.electro.tipoEnvio, dominio, fechaExpiracion);
                escribirCookie('operadorLogistico', data.electro.operadorLogistico, dominio, fechaExpiracion);
                escribirCookie('codigoPostal', data.electro.codigoPostal, dominio, fechaExpiracion);
                if (typeof data.electro.zonaPrecio !== 'undefined') {
                    escribirCookie('zonaPrecio', data.electro.zonaPrecio, dominio, fechaExpiracion);
                }
                cambios = true;
            }

            if (data && data.super) {
                if (data.super.haySucursalSuper === false) {
                    borrarCookie('Id-Sucursal-Super', dominio);
                    cambios = true;
                } else if (Array.isArray(data.super.sucursales) && data.super.sucursales.length > 0) {
                    const sucursalSeleccionada = data.super.sucursales.find(s => s.esDefault) || data.super.sucursales[0];
                    if (sucursalSeleccionada && sucursalSeleccionada.idSucursal) {
                        escribirCookie('Id-Sucursal-Super', sucursalSeleccionada.idSucursal, dominio, fechaExpiracion);
                        cambios = true;
                    }
                }
            }

            if (!cambios) {
                return;
            }

            params.delete('cp');
            params.delete('codigoPostal');
            const nuevaUrl = `${window.location.pathname}${params.toString() ? `?${params}` : ''}${window.location.hash}`;
            window.history.replaceState({}, '', nuevaUrl);

            if (typeof iniciarCabezal === 'function') {
                try {
                    iniciarCabezal();
                } catch (error) {
                    console.error('No se pudo actualizar el cabezal automáticamente:', error);
                    window.location.reload();
                    return;
                }
            } else {
                window.location.reload();
                return;
            }

            const modalCodigoPostal = document.getElementById('codigo-postal');
            if (modalCodigoPostal && typeof Foundation !== 'undefined' && Foundation && Foundation.Reveal) {
                try {
                    const instancia = Foundation.Reveal.getInstance(modalCodigoPostal) || new Foundation.Reveal($(modalCodigoPostal));
                    instancia.close();
                } catch (error) {
                    console.warn('No se pudo cerrar el modal de código postal:', error);
                }
            }
        })
        .catch(error => {
            console.error('No se pudo aplicar el código postal desde la URL:', error);

            if (typeof setCodigoPostalUnificado === 'function') {
                const inputCp = document.getElementById('idCodigoPostalUnificado');
                if (inputCp) {
                    inputCp.value = cpParam;
                    try {
                        setCodigoPostalUnificado();
                    } catch (fallbackError) {
                        console.error('Fallo el intento de aplicar el código postal con la función existente:', fallbackError);
                    }
                }
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    // Manejo de breadcrumbs
    const breadcrumbLinks = document.querySelectorAll('.breadcrumb-link');
    const currentPath = window.location.pathname;
    
    breadcrumbLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('selected');
        }
        
        link.addEventListener('click', function(e) {
            breadcrumbLinks.forEach(l => l.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    aplicarCodigoPostalDesdeQuery();
}); 
