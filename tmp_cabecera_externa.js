// Función para obtener el dominio base
function getBaseDomain() {
    const hostname = window.location.hostname;
    const port = window.location.port;

    // Check if hostname is an IP address
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (ipRegex.test(hostname)) {
        // If it's an IP address, return '/' to set cookies for the current domain
        return '';
    }

    const parts = hostname.split('.');

    // Si es un dominio sin punto (ej: laolweb)
    if (parts.length === 1) {
        return '.' + hostname;
    }

    const last = parts[parts.length - 1];
    const secondLast = parts.length > 1 ? parts[parts.length - 2] : '';

    // Manejar dominios con TLD de dos niveles (ej: com.ar, gob.ar, co.uk)
    const secondLevelTlds = ['com', 'org', 'net', 'gov', 'gob', 'edu', 'mil', 'co'];
    if (parts.length >= 3 && last.length === 2 && secondLevelTlds.includes(secondLast)) {
        return '.' + parts.slice(-3).join('.');
    }

    // Si tiene subdominios (ej: testing.laanonimaws.com)
    if (parts.length > 2) {
        return '.' + parts.slice(-2).join('.');
    }

    // Si es un dominio normal (ej: laanonimaws.com)
    return '.' + hostname;
}

const baseDomain = getBaseDomain();
let restableciendoCodigoPostalNoEmpleado = false;

// Safe stub: if agregar_al_carrito_01 is not defined, provide a no-op that returns true
if (typeof window.agregar_al_carrito_01 !== 'function') {
    window.agregar_al_carrito_01 = function () { return true; };
}

const INACTIVIDAD_MAXIMA_MS = 60 * 60 * 1000;
let temporizadorInactividad = null;

const reiniciarTemporizadorInactividad = () => {
    if (temporizadorInactividad) {
        clearTimeout(temporizadorInactividad);
    }
    temporizadorInactividad = setTimeout(() => {
        window.location.reload(true);
    }, INACTIVIDAD_MAXIMA_MS);
};

['mousemove', 'keydown', 'scroll', 'touchstart', 'click'].forEach(evento => {
    window.addEventListener(evento, reiniciarTemporizadorInactividad, { passive: true });
});

reiniciarTemporizadorInactividad();


// Function to update employee discount display
function actualizarDescuentoEmpleado(datosCliente, configuracionesEmpleado) {
    const liDescuentoEmpleado = document.getElementById('liDescuentoEmpleado');
    const montoDescuentoEmpleado = document.getElementById('montoDescuentoEmpleado');

    if (datosCliente && datosCliente.esEmpleado) {
        if (datosCliente.topeDescuento && datosCliente.topeDescuento > 0) {
            // Format the amount with thousands separator
            const montoFormateado = new Intl.NumberFormat('es-AR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(datosCliente.topeDescuento);

            montoDescuentoEmpleado.textContent = montoFormateado;
        } else {
            // Show that employee discount is being configured
            montoDescuentoEmpleado.textContent = 'Configurando...';
        }
        liDescuentoEmpleado.style.display = 'block';
        document.querySelector('.seleccionar-sucursal').style.display = 'none';

        const divEnvios = document.getElementById("divEnviosSelecta");

		if (divEnvios) {
  			divEnvios.style.display = "none";
		}

        // Configurar cookies para empleados con valores de configuración del servidor
        configurarCookiesEmpleado(configuracionesEmpleado);
    } else {
        liDescuentoEmpleado.style.display = 'none';
        document.querySelector('.seleccionar-sucursal').style.display = 'block';
    }
}

/**
 * Configura las cookies específicas para empleados usando los valores de configuración del servidor
 */
function configurarCookiesEmpleado(configuracionesEmpleado) {
    const fechaExpiracion = new Date();
    fechaExpiracion.setFullYear(fechaExpiracion.getFullYear() + 1);
    const expires = `expires=${fechaExpiracion.toUTCString()}`;
    const domain = `domain=${baseDomain}`;
    const secure = 'secure';
    const samesite = 'SameSite=None';

    // Usar valores de configuración del servidor
    const SUCURSAL_EMPLEADOS = configuracionesEmpleado?.SUCURSAL_EMPLEADOS || 152;
    const ZONA_PRECIO_EMPLEADOS = configuracionesEmpleado?.ZONA_PRECIO_EMPLEADOS || 5;
    const CODIGO_POSTAL_EMPLEADOS = configuracionesEmpleado?.CODIGO_POSTAL_EMPLEADOS || 1714;
    const SUCURSAL_ENTREGA_NOMBRE = configuracionesEmpleado?.SUCURSAL_ENTREGA_NOMBRE || 'Ituzaingo';

    // Setear cookies con valores de empleado
    document.cookie = `Id-Sucursal-Electro=${SUCURSAL_EMPLEADOS}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
    document.cookie = `codigoPostal=${CODIGO_POSTAL_EMPLEADOS}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
    document.cookie = `seleccionocp=1; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
    document.cookie = `idZonaPrecio=${ZONA_PRECIO_EMPLEADOS}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
    document.cookie = `descripcionLocalidadCabezal=${SUCURSAL_ENTREGA_NOMBRE}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;

    // Borrar cookie de sucursal super si existe
    const expiresPast = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';
    document.cookie = `Id-Sucursal-Super=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;

    // Actualizar la ubicación en el cabezal
    actualizarUbicacionCabezal();
}

/**
 * Bloquea el overlay de código postal para empleados
 */
function bloquearOverlayCodigoPostalEmpleados() {
    // Verificar si el usuario es empleado
    const esEmpleado = obtenerCookie('es_empleado') === '1' || obtenerCookie('es_empleado_v1') === '1';

    if (esEmpleado) {
        //console.log('Usuario es empleado - bloqueando overlay de código postal');

        // Función para bloquear completamente
        const bloquearCompletamente = () => {
            // 1. Buscar y bloquear el enlace principal
            const linkCodigoPostal = document.querySelector('a[data-toggle="codigo-postal"]');
            if (linkCodigoPostal) {
                // Remover todos los atributos relacionados con Foundation
                linkCodigoPostal.removeAttribute('data-toggle');
                linkCodigoPostal.removeAttribute('aria-controls');
                linkCodigoPostal.removeAttribute('aria-haspopup');
                linkCodigoPostal.removeAttribute('tabindex');

                // Agregar clase disabled y estilos
                linkCodigoPostal.classList.add('disabled');
                linkCodigoPostal.style.cursor = 'not-allowed';
                linkCodigoPostal.style.opacity = '0.5';
                linkCodigoPostal.style.pointerEvents = 'none';

                // Tooltip
                linkCodigoPostal.title = 'No se puede cambiar la ubicación para empleados';

                // Ocultar PERMANENTEMENTE el ícono de advertencia usando múltiples métodos
                const iconosAdvertencia = linkCodigoPostal.querySelectorAll('img[src*="icono-advertencia2.svg"], .icono-advertencia2, .ico-zona4');
                iconosAdvertencia.forEach(icono => {
                    icono.style.display = 'none';
                    icono.style.visibility = 'hidden';
                    icono.style.opacity = '0';
                    icono.remove(); // Remover completamente del DOM
                });

               // console.log('Enlace de código postal bloqueado');
            }

            // 2. Bloquear el overlay completamente
            const overlayCodigoPostal = document.getElementById('codigo-postal');
            if (overlayCodigoPostal) {
                // Remover atributos de Foundation
                overlayCodigoPostal.removeAttribute('data-reveal');
                overlayCodigoPostal.removeAttribute('data-close-on-click');
                overlayCodigoPostal.removeAttribute('data-animation-in');
                overlayCodigoPostal.removeAttribute('data-animation-out');

                // Ocultar completamente el overlay
                overlayCodigoPostal.style.display = 'none !important';
                overlayCodigoPostal.style.visibility = 'hidden';
                overlayCodigoPostal.style.opacity = '0';

                // Destruir instancia de Foundation si existe
                if (typeof $ !== 'undefined' && $(overlayCodigoPostal).data('zfPlugin')) {
                    $(overlayCodigoPostal).foundation('destroy');
                }

                //console.log('Overlay de código postal bloqueado');
            }

            // 3. Bloquear todos los eventos relacionados
            if (typeof $ !== 'undefined') {
                // Remover todos los listeners existentes
                $(document).off('click', '[data-toggle="codigo-postal"]');
                $(document).off('click', '.seleccionar-sucursal');

                // Agregar listener que bloquea cualquier intento
                $(document).on('click', 'a[data-toggle="codigo-postal"], .seleccionar-sucursal', function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    //console.log('Intento de abrir código postal bloqueado para empleado');
                    return false;
                });

                // Bloquear eventos de Foundation
                $(document).off('open.zf.reveal', '#codigo-postal');
                $(document).on('open.zf.reveal', '#codigo-postal', function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    return false;
                });
            }
        };

        // Ejecutar inmediatamente
        bloquearCompletamente();

        // También ejecutar después de delays para asegurar que Foundation esté cargado
        setTimeout(bloquearCompletamente, 100);
        setTimeout(bloquearCompletamente, 500);
        setTimeout(bloquearCompletamente, 1000);

        // Observer para detectar cambios en el DOM y re-bloquear
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(function (mutations) {
                let shouldReblock = false;
                mutations.forEach(function (mutation) {
                    if (mutation.type === 'childList' || mutation.type === 'attributes') {
                        // Verificar si se agregó o modificó algo relacionado con código postal
                        if (mutation.target && (
                            mutation.target.id === 'codigo-postal' ||
                            mutation.target.getAttribute && mutation.target.getAttribute('data-toggle') === 'codigo-postal' ||
                            (mutation.target.querySelector && mutation.target.querySelector('[data-toggle="codigo-postal"]'))
                        )) {
                            shouldReblock = true;
                        }
                    }
                });

                if (shouldReblock) {
                    setTimeout(bloquearCompletamente, 50);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-toggle', 'data-reveal', 'style', 'class']
            });
        }
    }
}

const iniciarCabezal = () => {

    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    const salirParam = urlParams.get('salir');
    const cicloParam = urlParams.get('ciclo');


    if (salirParam === '1') {
        const domain = `domain=${baseDomain}`;
        const secure = 'secure';
        const samesite = 'SameSite=None';
        const expiresPast = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';

        // Borrar cookie principal de acceso
        document.cookie = `access-token-unificacion=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;

        // Borrar cookies de empleado
        document.cookie = `es_empleado_v1=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;
        document.cookie = `es_empleado=; path=/; ${domain}; ${expiresPast}`;

        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, newUrl);
    }
    if(!getCookie("access-token-unificacion")){
        const domain = `domain=${baseDomain}`;
        const secure = 'secure';
        const samesite = 'SameSite=None';
        const expiresPast = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';
        // Borrar cookies de empleado
        document.cookie = `es_empleado_v1=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;
        document.cookie = `es_empleado=; path=/; ${domain}; ${expiresPast}`;
    }

    if (tokenParam) {
        const fechaExpiracion = new Date();
        fechaExpiracion.setFullYear(fechaExpiracion.getFullYear() + 1);
        const expires = `expires=${fechaExpiracion.toUTCString()}`;
        const domain = `domain=${baseDomain}`;
        const secure = 'secure';
        const samesite = 'SameSite=None';
        document.cookie = `access-token-unificacion=${tokenParam}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
        const newUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, newUrl);
    }

    if (cicloParam) {
        window.location.href = DOMINIO_MICUENTA + '/ciclo=' + cicloParam;
        return;
    }


    const token = obtenerCookie("access-token-unificacion");


    cargarDatosUsuario();

    // Hide link_super if Id-Sucursal-Super cookie doesn't exist
    if (!obtenerCookie("Id-Sucursal-Super")) {
        $("#link_super").hide();
	} else {
        $("#link_super").show();
    }

    actualizarUbicacionCabezal();

    // Interceptar clic en "Cerrar Sesión" para borrar cookies de empleado
    interceptarCerrarSesion();
};

/**
 * Intercepta el clic en "Cerrar Sesión" para borrar cookies antes de salir
 */
function interceptarCerrarSesion() {
    const linkSalir = document.getElementById('liCuentaSalir');
    if (linkSalir) {
        const enlaceSalir = linkSalir.querySelector('a');
        if (enlaceSalir) {
            enlaceSalir.addEventListener('click', function (e) {
                // Borrar cookies de empleado antes de salir
                borrarCookiesEmpleado();

                // Permitir que el enlace continue normalmente
                // No se previene el default para que vaya al DOMINIO_MICUENTA
            });
        }
    }
}

/**
 * Borra las cookies de empleado y de sesión
 */
function borrarCookiesEmpleado() {
    const domain = `domain=${baseDomain}`;
    const secure = 'secure';
    const samesite = 'SameSite=None';
    const expiresPast = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';

    // Borrar cookie principal de acceso
    document.cookie = `access-token-unificacion=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;

    // Borrar cookies de empleado
    document.cookie = `es_empleado_v1=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;
    document.cookie = `es_empleado=; path=/; ${domain}; ${expiresPast}`;

    // Ocultar el elemento de descuento empleado inmediatamente
    const liDescuentoEmpleado = document.getElementById('liDescuentoEmpleado');
    if (liDescuentoEmpleado) {
        liDescuentoEmpleado.style.display = 'none';
    }
}

const actualizarUbicacionCabezal = () => {

    if (obtenerCookie("descripcionLocalidadCabezal") && obtenerCookie("codigoPostal") && obtenerCookie("descripcionLocalidadCabezal") != "Seleccione...") {
        $(".sucursal.cortar-texto-1").html(`${unescape(obtenerCookie("descripcionLocalidadCabezal"))} (${obtenerCookie("codigoPostal")})`);
    } else {
        $(".sucursal.cortar-texto-1").html("Seleccione...")
    }

    if (obtenerCookie("codigoPostal") == "HB018305") {
        $(".sucursal.cortar-texto-1").html(`${unescape(obtenerCookie("descripcionLocalidadCabezal"))}`);
    }

    if (obtenerCookie("tipoEnvioUnificado") == 0 || getCookie("codigoPostal") == "HB018305") {
        $(".colorffffff.font-size-14.bold.line-height-1.seleccionar-sucursal").addClass("zona4");
        $(".font-size-24.color000000.mb-3.text-center.titulo-cp-modal").addClass("zona4");
        $(".font-size-16.color989898.text-center.parrafo-cp-modal").addClass("zona4");
        $(".font-size-24.color000000.mb-3.text-center.titulo-cp-modal").html("Ups!!!<br>Todav&iacute;a no llegamos a tu localidad.");
        $(".font-size-16.color989898.text-center.parrafo-cp-modal").html("Pod&eacute;s cerrar esta ventana y seguir visitando nuestro sitio, o cambiar el c&oacute;digo postal para elegir una localidad a la que lleguemos.");
    }

}

const cargarDatosUsuario = () => {
    const accessToken = obtenerCookie('access-token-unificacion');
    const cartToken = obtenerCookie('cart-token');
    const fechaExpiracion = new Date();
    fechaExpiracion.setFullYear(fechaExpiracion.getFullYear() + 1);
    const expires = `expires=${fechaExpiracion.toUTCString()}`;
    const domain = `domain=${baseDomain}`;
    const secure = 'secure';
    const samesite = 'SameSite=None';
    const portada_actual_id = document.getElementById('portada-actual-id')?.value ?? '';
    const portada_actual_tipo = document.getElementById('portada-actual-tipo')?.value ?? '';
    const pagina_actual_href = btoa(location.href)
    // Buscar elementos con data-codigo-producto
    const productosEnPagina = [];
    const elementosProducto = document.querySelectorAll('[id-codigo-producto]');
    elementosProducto.forEach(elemento => {

        const codigoProducto = elemento.getAttribute('id-codigo-producto');
        if (codigoProducto) {
            productosEnPagina.push(codigoProducto);
        }

    });

    $.ajax({
        url: DOMINIO_WEB + '/sitio/cabecera/datos',
        type: 'POST',
        dataType: 'json',
        crossDomain: true,

        data: {
            productosEnPagina: productosEnPagina,
            portada_actual_id: portada_actual_id,
            portada_actual_tipo: portada_actual_tipo,
            pagina_actual_href: pagina_actual_href
        },
        xhrFields: {
            withCredentials: true  // NECESARIO para que se envíen cookies a subdominios
        },
        success: function (response) {
            if (response && response.clienteUnificado && response.clienteUnificado.nombre) {
                $('.nombre-usuario').text(response.clienteUnificado.nombre);
                $('.nombre-usuario-mobile').text("Mi Cuenta");
                $("#btn-abrir_menu_usuario").removeAttr("onClick");
                $("#btn-abrir_menu_usuario").attr("href", DOMINIO_MICUENTA + "/misdatos");
                // document.cookie = `laanonimaclienteunificado=${response.clienteUnificado.idCliente}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
                // document.cookie = `dinf=${response.clienteUnificado.dinf}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
                setCookie('dinf', response.clienteUnificado.dinf, 30);
                setCookie('dni', response.clienteUnificado.DNI, 1 / 1440);


                $("#liCuentaRegistro, #liCuentaIngresar").remove();
                $("#liCuentaIngresarMobile, #liCuentaRegistroMobile").remove();

                // Update employee discount display directly with AJAX response
                actualizarDescuentoEmpleado(response.clienteUnificado, response.configuracionesEmpleado);

                // Si es empleado: setear cookies necesarias desde la respuesta
                try {
                    if (response && response.clienteUnificado && response.clienteUnificado.esEmpleado) {
                        const isHttps = window.location.protocol === 'https:';
                        const fechaExpiracion = new Date();
                        fechaExpiracion.setFullYear(fechaExpiracion.getFullYear() + 1);
                        const expires = `expires=${fechaExpiracion.toUTCString()}`;
                        const domain = baseDomain ? `domain=${baseDomain}` : '';
                        const secure = isHttps ? 'secure' : '';
                        const samesite = isHttps ? 'SameSite=None' : 'SameSite=Lax';

                        // marcar empleado
                        document.cookie = `es_empleado=1; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
                        document.cookie = `es_empleado_v1=1; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;

                        // sucursal electro desde la respuesta (fallback a config)
                        const sucElectro = (response.clienteUnificado.idSucursalEntregaElectro ||
                                            response.configuracionesEmpleado?.SUCURSAL_EMPLEADOS || '')
                        if (sucElectro !== '') {
                            document.cookie = `Id-Sucursal-Electro=${sucElectro}; path=/; ${domain}; ${expires}; ${secure}; ${samesite}`;
                        }

                        // eliminar sucursal super
                        const expiresPast = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';
                        document.cookie = `Id-Sucursal-Super=; path=/; ${domain}; ${expiresPast}; ${secure}; ${samesite}`;
                    }
                } catch (e) {
                    console.error('No se pudieron aplicar cookies de empleado desde la respuesta', e);
                }

            } else {
                $("#liCuentaDatos").remove();
                $("#liCuentaSalir").remove();
                $("#liCuentaDatosMobile").remove();
                $("#liCuentaSalirMobile").remove();
            }


            const codigoPostalActual = (obtenerCookie('codigoPostal') || '').trim();
            const esEmpleadoCliente = Boolean(response?.clienteUnificado?.esEmpleado);
            const esCodigoPostalEmpleado = codigoPostalActual === '1714';

            if (!esEmpleadoCliente && esCodigoPostalEmpleado && !restableciendoCodigoPostalNoEmpleado) {
                restableciendoCodigoPostalNoEmpleado = true;
                ponerCPDefault();
            }

            $('#total_carrito').text(response.carrito?.cantidad ?? 0);
            $('#total_carrito_mobile').text(response.carrito?.cantidad ?? 0);
            // if (response.carrito.cantidadElectro > 0) {
            //     $('.electro').show();
            // } else {
            //     $('.electro').hide();
            // }
            // if (response.carrito.cantidadFood > 0) {
            //     $('.menu.carrito .supermercado').show();
            // } else {
            //     $('.menu.carrito .supermercado').hide();
            // }
            // if (response.carrito.cantidad === 0 && response.carrito.cantidadElectro === 0 && response.carrito.cantidadFood === 0) {
            //     $('.menu-carrito-submenu').hide();
            // } else {
            //     $('.menu-carrito-submenu').show();
            // }
            if (response.carrito.cantidadElectro == 0 && response.carrito.cantidadFood > 0) {
                $('#linkCarrito').attr('href', DOMINIO_CARRITO_SUPER);
            }
            var sinStock = false;
            // Handle stock validation
            if (response.stockProductos) {
                Object.entries(response.stockProductos).forEach(([codigoProducto, stock]) => {

                    if (stock <= 0) {
                        var elementoProducto = $(`[id-codigo-producto="${codigoProducto}"]`);


                        elementoProducto.remove();
                        sinStock = true;

                    }
                });
                if (typeof catalogoProgressiveLoading === 'function') {
                    catalogoProgressiveLoading();
                }


                if (typeof $.fn.slick !== 'undefined' && sinStock) {
                    $('.carusel').each(function () {
                        if ($(this).hasClass('slick-initialized')) {
                            $(this).slick('unslick');
                        }
                        $(this).slick({
                            dots: true,
                            infinite: false,
                            speed: 300,
                            slidesToShow: 4,
                            slidesToScroll: 1,
                            responsive: [
                                {
                                    breakpoint: 1024,
                                    settings: {
                                        slidesToShow: 3,
                                        slidesToScroll: 1
                                    }
                                },
                                {
                                    breakpoint: 600,
                                    settings: {
                                        slidesToShow: 2,
                                        slidesToScroll: 1
                                    }
                                },
                                {
                                    breakpoint: 480,
                                    settings: {
                                        slidesToShow: 1,
                                        slidesToScroll: 1
                                    }
                                }
                            ]
                        });
                    });
                }

            }
            if (!obtenerCookie("Id-Sucursal-Super")) {
                $('a[href="/supermercado/"]').hide();
            } 

            if (response.cartProductos) {
                response.cartProductos.forEach(productosArray => {
                    productosArray.forEach(producto => {
                        agregar_al_carrito_01(producto.codigo)

                        console.log(producto.cantidad)
                        if (producto.idEcmsCarrito) {
                            document.querySelectorAll(`#agregado_${producto.codigo}`).forEach((agregadoBtn) => {
                                $(agregadoBtn).find('.input-group-field').val(producto.cantidad);
                                $(agregadoBtn).find('.input-group-label.menos').attr('data-codigo', producto.idEcmsCarrito);
                                $(agregadoBtn).find('.input-group-label.mas').attr('data-codigo', producto.idEcmsCarrito);
                            })
                        }
                        if (producto.id) {
                            document.querySelectorAll(`#agregado_${producto.codigo}`).forEach((agregadoBtn) => {
                                $(agregadoBtn).find('.input-group-field').val(producto.cantidad);
                                $(agregadoBtn).find('.input-group-label.menos').attr('data-codigo', producto.id);
                                $(agregadoBtn).find('.input-group-label.mas').attr('data-codigo', producto.id);
                            })
                        }
                    });
                });
            }
            for (const favoritos of response.favoritos) {
                if (favoritos.contenido.length > 0) {
                    for (const fav of favoritos.contenido) {
                        $(`#btn_favorito[data-codigo="${fav.id}"]`).addClass("fav_activo"); //electro
                    }
                }
            }

            // if (response.favoritos && response.favoritos.total) {
            //     for (const favorito of response.favoritos.contenido) {
            //         // $(`#btn_favorito[data-codigo="${favorito.codigo}"]`).addClass("fav_activo"); //food
            //         $(`#btn_favorito[data-codigo="${favorito.id}"]`).addClass("fav_activo"); //electro
            //     }
            // }

            $('.dropdown.menu.categorias').addClass('foundation-inicializado');
            $('.menu.n1.submenu.is-dropdown-submenu.first-sub.vertical').css('display', '');
            $('.dropdown.menu.menu-servicios').addClass('foundation-inicializado');
            $('.menu.servicios.submenu.is-dropdown-submenu.first-sub.vertical').css('display', '');
        },
        error: function (error) {
            console.error('Error al cargar datos del usuario:', error);
        }
    });
};


const setCodigoPostalUnificado = () => {
    $("#msgCodigoPostal").html("");
    const idCp = $("#idCodigoPostalUnificado").val();

    if (idCp.length < 4) {
        $('#div_noSeMiCodigo').slideDown(150);
        $('#divBtnSeleccionarSucursal').slideUp(150);
        $('#opcionesSucursal').slideUp(150);
        $('#infoCodigoPostal').slideDown(150);
        return false;
    }

    if (!idCp) {
        $("#msgCodigoPostal").html("Ingrese c&oacute;digo postal.");
        return false;
    }

    $('#divBtnSeleccionarSucursal').slideUp(150);
    $('#opcionesSucursal').slideUp(150);
    $('#infoCodigoPostal').slideDown(150);
    // let extra = ""
    // if(getCookie("access-token-unificacion")){
    //     extra = '&token=' + getCookie("access-token-unificacion");
    // }
    fetch(DOMINIO_WEB + '/sucursal/' + idCp, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        },
        credentials: 'include'
    })
        .then(response => response.json())
        .then(response => {
            // Guardar la respuesta en variable global
            respuestaServidor = response;
            if (response.electro && response.electro.existeSucursal) {
                setCookie('Id-Sucursal-Electro', response.electro.idSucursalVirtualTecno, 30);
                setCookie('descripcionLocalidadCabezal', response.electro.descripcionLocalidadCabezal, 30);
                setCookie('tipoEnvioUnificado', response.electro.tipoEnvio, 30);
                setCookie('operadorLogistico', response.electro.operadorLogistico, 30);
                setCookie('codigoPostal', response.electro.codigoPostal, 30);
                setCookie('idZonaPrecio', response.electro.idZonaPrecio, 30);


                document.cookie = `laanonimasucursalnombreentrega=; path=/; domain=${baseDomain}; expires=Thu, 01 Jan 1970 00:00:00 UTC; secure; SameSite=None`;

            }

            if (response.super && response.super.haySucursalSuper === false) {
                setCookie('Id-Sucursal-Super', '', -1);
                // No hacer return aquí, continuar para procesar sucursales informativas
            }

            if (response.error == true && response.cpc == true) {
                $("#msgCodigoPostal").html(response.mensaje);
                $('#div_noSeMiCodigo').slideDown(150);
            }

            if (response.super && response.super.haySucursalSuper) {
                let opciones = '';
                if (response.super.sucursales.length === 1 && response.super.sucursales[0].idSucursal == 161) {
                    setCookie('codigoPostal', idCp, 30);
                    setCookie('descripcionLocalidadCabezal', response.super.sucursales[0].descLocalidad, 30);
                    setCookie('Id-Sucursal-Electro', 0, 30);
                }
                if (response.super.sucursales.length === 1) {
                    /* food == 1 */
                    opciones += `
                        <input type='radio' name='sucursalSuper' value='${response.super.sucursales[0].idSucursal}' id='sucursal_${response.super.sucursales[0].idSucursal}' data-sucursal='${response.super.sucursales[0].descLocalidad}' >
                        <label for='sucursal_${response.super.sucursales[0].idSucursal}'>
                            ${response.super.sucursales[0].descLocalidad}
                            <span>${response.super.sucursales[0].direccion}</span>
                        </label>
                    `;
                    let btnSetSucursal = "<button class='button expanded rounded font-size-16 bold' id='btn_setSucursalSuper' onclick='setSucursalSuper()' style='display:none;'>Confirmar</button>";
                    
                    $("#opcionesSucursal").html(opciones);
                    $("#divBtnSeleccionarSucursal").html(btnSetSucursal);
                    $('#divBtnSeleccionarSucursal').slideDown(150);
                    // Asegurar que el contenedor se muestre (para ver informativas también)
                    $('#opcionesSucursal').slideDown(150);
                    $('#infoCodigoPostal').slideUp(150);
                    $('#div_noSeMiCodigo').slideUp(150);
                } else {
                    /* Foood > 1 */
                    response.super.sucursales.forEach(sucursal => {
                        const esSoloInformatica = sucursal.soloInformatica || false;
                        opciones += `
                            <input type='radio' name='sucursalSuper' value='${sucursal.idSucursal}' id='sucursal_${sucursal.idSucursal}' data-sucursal='${sucursal.descLocalidad}' data-solo-informatica='${esSoloInformatica}'>
                            <label for='sucursal_${sucursal.idSucursal}'>
                                <u>${sucursal.descLocalidad}</u>
                                <span>${sucursal.direccion}</span>
                            </label>
                        `;
                    });
                    let btnSetSucursal = "<button class='button expanded rounded font-size-16 bold ' style='display: none;' id='btn_setSucursalSuper' onclick='setSucursalSuper()'>Confirmar</button>";
                    $("#divBtnSeleccionarSucursal").html(btnSetSucursal);
                    $('#divBtnSeleccionarSucursal').slideDown(150);
                    $('#idCodigoPostalUnificado').addClass('editar');

                    $("#opcionesSucursal").html(opciones);
                    $('#opcionesSucursal').slideDown(150);
                    $('#infoCodigoPostal').slideUp(150);
                    $('#div_noSeMiCodigo').slideUp(150);
                    $('#divBtnSeleccionarSucursal').stop(true, true).slideUp(150, function () {
                        $(this).empty();
                    });

                }
                $('input[name="sucursalSuper"]').on('change', function () {
                    const selectedValue = $(this).val();
                    $('input[name="sucursalInformativa"]').each(function () {
                        $(this).prop('checked', false);
                    });

                    if (selectedValue) {
                        actualizarFuncion();
                        let btnSetSucursal = "<button class='button expanded rounded font-size-16 bold '  id='btn_setSucursalSuper' onclick='setSucursalSuper()'>Confirmar</button>";
                        $("#divBtnSeleccionarSucursal").html(btnSetSucursal);
                        $('#divBtnSeleccionarSucursal').slideDown(150);

                        $('#btn_setSucursalSuper').slideDown(150);
                    } else {
                        $('#btn_setSucursalSuper').slideUp(150);
                    }
                });
            }

            // Manejar sucursales informativas - siempre procesar si existen
            if (response.sucursalesInformativas && response.sucursalesInformativas.length > 0) {
                let opcionesInformativas = '';
                response.sucursalesInformativas.forEach(sucursal => {
                    opcionesInformativas += `
                        <input type='radio' name='sucursalInformativa' value='${sucursal.idSucursal}' id='sucursal_inf_${sucursal.idSucursal}' data-sucursal='${sucursal.descLocalidad}'>
                        <label for='sucursal_inf_${sucursal.idSucursal}'>
                            <u>${sucursal.descLocalidad}</u>
                            <span>${sucursal.direccion}</span>
                        </label>
                    `;
                });

                // Si no hay sucursales de super, mostrar solo las informativas
                if (!response.super || !response.super.haySucursalSuper) {
                    $("#opcionesSucursal").html(opcionesInformativas);
                    $('#opcionesSucursal').slideDown(150);
                    $('#div_noSeMiCodigo').slideUp(150);
                } else {
                    // Si hay sucursales de super, agregar las informativas después
                    $("#opcionesSucursal").append(opcionesInformativas);
                    $('#opcionesSucursal').slideDown(150);
                }

                // Agregar evento para sucursales informativas
                $('input[name="sucursalInformativa"]').on('change', function () {
                    const selectedValue = $(this).val();
                    $('input[name="sucursalSuper"]').each(function () {
                        $(this).prop('checked', false);
                    });

                    if (selectedValue) {
                        // Mostrar botón confirmar para sucursales informativas
                        let btnSetSucursal = "<button class='button expanded rounded font-size-16 bold ' id='btn_setSucursalInformativa' onclick='setSucursalInformativa()'>Confirmar</button>";
                        $("#divBtnSeleccionarSucursal").html(btnSetSucursal);
                        $('#divBtnSeleccionarSucursal').slideDown(150);
                    }
                });
            } else {
                $('#div_noSeMiCodigo').slideUp(150);

                // Caso: sólo Electro (sin Super ni informativas) -> mostrar botón Confirmar
                if ((!(response.super && response.super.haySucursalSuper)) && (!response.sucursalesInformativas || response.sucursalesInformativas.length === 0) && (response.electro && response.electro.existeSucursal)) {
                    let btnSetSucursal = "<button class='button expanded rounded font-size-16 bold ' id='btn_setSoloElectro' onclick='setSucursalInformativa()'>Confirmar</button>";
                    $("#divBtnSeleccionarSucursal").html(btnSetSucursal);
                    $('#divBtnSeleccionarSucursal').slideDown(150);
                }
            }


        })
        .catch(() => {
            $('#opcionesSucursal').slideUp(150);
            $('#infoCodigoPostal').slideDown(150);
            $('#div_noSeMiCodigo').slideDown(150);
            $("#msgCodigoPostal").html("Error al obtener la información.");
        });

    actualizarUbicacionCabezal();

};

function actualizarFuncion() {
    const selectedRadio = document.querySelector('input[name="sucursalSuper"]:checked');

    if (selectedRadio) {
        $('#btn_setSucursalSuper').slideDown(150);
    }
}


const setSucursalElectro = () => {
    // document.cookie = `Id-Sucursal-Super=; path=/; ${domain}; expires=Thu, 01 Jan 1970 00:00:00 UTC; ${secure}; ${samesite}`;
    location.reload(true);
    return true;
}

// Variable global para almacenar la respuesta del servidor
let respuestaServidor = null;
let ultimaSucursalInformativaSeleccionada = null;

const setSucursalInformativa = (idSucursalInformativa = null) => {
    const sucursalInformativaSeleccionada = idSucursalInformativa || ultimaSucursalInformativaSeleccionada;
    const datosRespuesta = respuestaServidor || {};
    const datosElectro = datosRespuesta.electro || null;

    if (datosElectro && datosElectro.existeSucursal) {
        // Setear cookies con los datos de electro usando la función setCookie existente
        setCookie('Id-Sucursal-Electro', datosElectro.idSucursalVirtualTecno, 30);
        setCookie('descripcionLocalidadCabezal', datosElectro.descripcionLocalidadCabezal, 30);
        setCookie('tipoEnvioUnificado', datosElectro.tipoEnvio, 30);
        setCookie('operadorLogistico', datosElectro.operadorLogistico, 30);
        setCookie('codigoPostal', datosElectro.codigoPostal, 30);
        if (datosElectro.idZonaPrecio) {
            setCookie('idZonaPrecio', datosElectro.idZonaPrecio, 30);
        }
    }

    if (sucursalInformativaSeleccionada && Array.isArray(datosRespuesta.sucursalesInformativas)) {
        const sucursalInformativa = datosRespuesta.sucursalesInformativas.find(
            sucursal => String(sucursal.idSucursal) === String(sucursalInformativaSeleccionada)
        );

        if (sucursalInformativa) {
            if (sucursalInformativa.descLocalidad) {
                setCookie('descripcionLocalidadCabezal', sucursalInformativa.descLocalidad, 30);
            }
            if (sucursalInformativa.codigoPostal) {
                setCookie('codigoPostal', sucursalInformativa.codigoPostal, 30);
            }
            if (sucursalInformativa.idZonaPrecio) {
                setCookie('idZonaPrecio', sucursalInformativa.idZonaPrecio, 30);
            }
        }
    }

    // Al seleccionar una sucursal informativa, eliminar cookie de sucursal super
    setCookie('Id-Sucursal-Super', '', -1);

    // Cerrar el popup
    $('#codigo-postal').foundation('close');

    limpiarSeleccionCodigoPostal();
    location.reload();
}


const setSucursalSuper = (idSucursalSeleccionada = null) => {
    let sucursalSeleccionada = null;
    let idSeleccion = idSucursalSeleccionada;

    if (idSeleccion) {
        sucursalSeleccionada = $(`input[name='sucursalSuper'][value='${idSeleccion}']`);
    } else {
        sucursalSeleccionada = $("input[name='sucursalSuper']:checked");
        idSeleccion = sucursalSeleccionada.val();
    }

    if (!sucursalSeleccionada || !sucursalSeleccionada.length || !idSeleccion) {
        $("#opcionesSucursal").html("Por favor, seleccione una sucursal.");
        return;
    }

    const esSoloInformatica = sucursalSeleccionada.data('solo-informatica');

    if (idSeleccion) {
        let idSucursalParaCookie = idSeleccion;

        // Si la sucursal seleccionada es solo informativa, buscar la primera sucursal no informativa
        if (esSoloInformatica) {
            const primeraSucursalSuper = $("input[name='sucursalSuper']:not([data-solo-informatica='true'])").first();
            if (primeraSucursalSuper.length > 0) {
                idSucursalParaCookie = primeraSucursalSuper.val();
            }
        }

        // Setear cookie con la sucursal correcta
        setCookie('Id-Sucursal-Super', idSucursalParaCookie, 30);

        limpiarSeleccionCodigoPostal();
        location.reload();
    } else {
        $("#opcionesSucursal").html("Por favor, seleccione una sucursal.");
    }
};


const limpiarSeleccionCodigoPostal = () => {
    $("#btnCerrarCodigoPostal").click();
    $("#opcionesSucursal, #msgCodigoPostal, #idCodigoPostalUnificado").html('');
    ultimaSucursalInformativaSeleccionada = null;
};

const seleccionarSucursalSuper = (selectedValue) => {
    if (!selectedValue) {
        return;
    }

    ultimaSucursalInformativaSeleccionada = null;

    $('input[name="sucursalInformativa"]').each(function () {
        $(this).prop('checked', false);
    });

    const ejecutarSeleccion = () => setSucursalSuper(selectedValue);

    const $contenedorBoton = $('#divBtnSeleccionarSucursal');
    if ($contenedorBoton.length) {
        $contenedorBoton.stop(true, true).slideUp(150, function () {
            $(this).empty();
            ejecutarSeleccion();
        });
    } else {
        ejecutarSeleccion();
    }
};

const seleccionarSucursalInformativa = (selectedValue) => {
    if (!selectedValue) {
        return;
    }

    ultimaSucursalInformativaSeleccionada = selectedValue;

    $('input[name="sucursalSuper"]').each(function () {
        $(this).prop('checked', false);
    });

    const $contenedorBoton = $('#divBtnSeleccionarSucursal');
    if ($contenedorBoton.length) {
        $contenedorBoton.stop(true, true).slideUp(150, function () {
            $(this).empty();
            setSucursalInformativa(selectedValue);
        });
    } else {
        setSucursalInformativa(selectedValue);
    }
};

$(document).off('change.sucursalInformativa').on('change.sucursalInformativa', 'input[name="sucursalInformativa"]', function () {
    const selectedValue = $(this).val();
    seleccionarSucursalInformativa(selectedValue);
});

$(document).off('change.sucursalSuper').on('change.sucursalSuper', 'input[name="sucursalSuper"]', function () {
    const selectedValue = $(this).val();
    seleccionarSucursalSuper(selectedValue);
});

const obtenerCookie = (nombre) => {
    const cookies = document.cookie.split('; ');
    for (let cookie of cookies) {
        const [clave, valor] = cookie.split('=');
        if (clave === nombre) return valor;
    }
    return null;
};

// Search functionality
document.addEventListener('DOMContentLoaded', async function () {

    async function cargarRecursosFoundation() {
        const head = document.head;
        const body = document.body;

        // jQuery
        if (typeof window.jQuery === 'undefined') {
            const jqueryScript = document.createElement('script');
            jqueryScript.src = 'https://static-api.laanonima.com.ar//js/lib/jquery-3.7.1.min.js';
            jqueryScript.type = 'text/javascript';
            body.appendChild(jqueryScript);
        }
        // Foundation CSS
        const foundationCssLoaded = [...document.styleSheets].some(sheet =>
            sheet.href && sheet.href.includes('foundation')
        );
        if (!foundationCssLoaded) {
            const foundationCss = document.createElement('link');
            foundationCss.rel = 'stylesheet';
            foundationCss.href = 'https://static-api.laanonima.com.ar//css/foundation.css';

            const head = document.head;
            const firstLinkOrStyle = head.querySelector('link[rel="stylesheet"], style');

            if (firstLinkOrStyle) {
                head.insertBefore(foundationCss, firstLinkOrStyle);
            } else {
                head.appendChild(foundationCss); // si no hay otros estilos, lo agrega igual
            }
        }

        // Foundation JS
        const foundationLoaded = typeof window.Foundation !== 'undefined';
        if (!foundationLoaded) {
            const foundationScript = document.createElement('script');
            foundationScript.src = 'https://static-api.laanonima.com.ar//js/lib/foundation.js';
            foundationScript.onload = () => {
                //$(document).foundation();
                $(".cabezal, .cabezal2, .mobile").foundation();
                iniciar();

            };
            body.appendChild(foundationScript);
        } else {
            //$(document).foundation();
            $(".cabezal, .cabezal2, .mobile").foundation();
            iniciar();

        }

        //agregeo al menu una clase
        $('.dropdown.menu.categorias').addClass('foundation-inicializado');
        $('.menu.n1.submenu.is-dropdown-submenu.first-sub.vertical').css('display', '');
        $('.dropdown.menu.menu-servicios').addClass('foundation-inicializado');
        $('.menu.servicios.submenu.is-dropdown-submenu.first-sub.vertical').css('display', '');

    }
    await cargarRecursosFoundation();

    function iniciar() {

        // Verificar si el usuario es empleado
        const esEmpleado = obtenerCookie('es_empleado') === '1' || obtenerCookie('es_empleado_v1') === '1';

        // Solo abrir overlay si no es empleado y faltan cookies
        if (!esEmpleado && (!obtenerCookie("Id-Sucursal-Electro") || !obtenerCookie("codigoPostal") || !obtenerCookie("descripcionLocalidadCabezal"))) {
            $('#codigo-postal').foundation('open');
            ponerCPDefault()
        }
        iniciarCabezal();

        // Bloquear overlay de código postal para empleados
        bloquearOverlayCodigoPostalEmpleados();

    }
    $(document).on('click', '.reveal-overlay, [data-close]', function(e) {
        if ($('#codigo-postal').parent('.reveal-overlay').css('display') === 'block') {
            $('html').removeClass('is-reveal-open');
            $('body').css('overflow', '');
            $("#codigo-postal").css('opacity', 1)
            $("#codigo-postal").css('display', 'block')
        }
    });
});


function abrir_menu_categorias() {
    $("#menu-categorias-mobile").addClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-abrir_menu_categorias").slideUp(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);

    $("#btn-cerrar_menu_categorias").slideDown(0);
    $("#btn-cerrar_menu_servicios").slideUp(0);
    $("#btn-cerrar_menu_carrito").slideUp(0);
    $("#btn-cerrar_menu_usuario").slideUp(0);
}

function cerrar_menu_categorias() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-cerrar_menu_categorias").slideUp(0);

    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);
}

function abrir_menu_servicios() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").addClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);
    $("#btn-abrir_menu_servicios").slideUp(0);
    $("#btn-cerrar_menu_servicios").slideDown(0);
    $("#btn-cerrar_menu_categorias").slideUp(0);
    $("#btn-cerrar_menu_carrito").slideUp(0);
    $("#btn-cerrar_menu_usuario").slideUp(0);
}

function cerrar_menu_servicios() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-cerrar_menu_servicios").slideUp(0);
    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);
}

function abrir_menu_carrito() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").addClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-abrir_menu_carrito").slideUp(0);

    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);

    $("#btn-cerrar_menu_carrito").slideDown(0);
    $("#btn-cerrar_menu_categorias").slideUp(0);
    $("#btn-cerrar_menu_servicios").slideUp(0);;
    $("#btn-cerrar_menu_usuario").slideUp(0);
}

function cerrar_menu_carrito() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");
    $("#btn-cerrar_menu_carrito").slideUp(0);
    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);
}

function abrir_menu_usuario() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").addClass("abierto");

    $("#btn-abrir_menu_usuario").slideUp(0);
    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);

    $("#btn-cerrar_menu_usuario").slideDown(0);
    $("#btn-cerrar_menu_categorias").slideUp(0);
    $("#btn-cerrar_menu_servicios").slideUp(0);
    $("#btn-cerrar_menu_carrito").slideUp(0);

}

function cerrar_menu_usuario() {
    $("#menu-categorias-mobile").removeClass("abierto");
    $("#menu-servicios-mobile").removeClass("abierto");
    $("#menu-carrito-mobile").removeClass("abierto");
    $("#menu-usuario-mobile").removeClass("abierto");

    $("#btn-cerrar_menu_usuario").slideUp(0);
    $("#btn-abrir_menu_categorias").slideDown(0);
    $("#btn-abrir_menu_servicios").slideDown(0);
    $("#btn-abrir_menu_carrito").slideDown(0);
    $("#btn-abrir_menu_usuario").slideDown(0);

}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, days = 30) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const domain = window.location.hostname;
    const parts = domain.split('.');
    const rootDomain = parts.length > 2 && parts[parts.length - 1] === 'ar' && parts[parts.length - 2] === 'com'
        ? '.' + parts.slice(-3).join('.')
        : '.' + parts.slice(-2).join('.');
    document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/; domain=${rootDomain}; secure; samesite=Lax`;

    if (name === 'codigoPostal') {
        const valorValido = typeof value === 'string' ? value.trim() !== '' : Boolean(value);
        const debePersistir = days > 0 && valorValido;
        const flagDays = debePersistir ? days : -1;
        const flagDate = new Date();
        flagDate.setTime(flagDate.getTime() + (flagDays * 24 * 60 * 60 * 1000));
        const flagValue = debePersistir ? '1' : '';
        document.cookie = `seleccionocp=${flagValue}; expires=${flagDate.toUTCString()}; path=/; domain=${rootDomain}; secure; samesite=Lax`;
    }
}

function ponerCPDefault() {
    $.ajax({
        url: DOMINIO_WEB + '/sitio/sucursalDefault',
        type: 'GET',
        dataType: 'json',
        crossDomain: true,

        data: {
        },
        xhrFields: {
            withCredentials: true  // NECESARIO para que se envíen cookies a subdominios
        },
        success: function (response) {
            if (response) {
                // Set cookie with 30 days expiration using the new function
                setCookie('descripcionLocalidadCabezal', response.electro.descripcionLocalidadCabezal, 30);
                setCookie('Id-Sucursal-Electro', response.electro.idSucursalVirtualTecno, 30);
                setCookie('Id-Sucursal-Super', response.super.idSucursal, 30);
                setCookie('codigoPostal', response.defaultCP, 30);

                setCookie("ciudad", response.electro.descripcionLocalidadCabezal, 30)
                setCookie("ciudad_id", response.electro.idLocalidad, 30)
                setCookie("provincia", response.electro.descProvincia, 30)
                setCookie("provincia_id", response.electro.idProvincia, 30)
                setCookie("tipoEnvioUnificado", response.electro.tipoEnvio, 30)

                setCookie('operadorLogistico', response.electro.operadorLogistico, 30);
                setCookie('idZonaPrecio', response.electro.idZonaPrecio, 30);

                actualizarUbicacionCabezal()

                if (response.electro.tipoEnvio != 0) {
                    $(".Super").show()
                }

            } else if (response.error) {
                throw new Error(response.error);
            }
        },
        error: function (error) {
            console.error('Error:', error);
        }
    });

}

//agrego para la push notificacion
function mostrarPushNotificacion() {
    const path = window.location.pathname.toLowerCase().replace(/\/+$/, '');
    const notificaciones = window.notificacionesPopUp || [];

    function getCookie(nombre) {
        const valor = `; ${document.cookie}`;
        const partes = valor.split(`; ${nombre}=`);
        if (partes.length === 2) return partes.pop().split(';').shift();
    }

    if (!getCookie('codigoPostal')) {
        console.log('Falta cookie codigoPostal');
        return;
    }

    // Buscar primero una notificación global con prioridad
    for (const popup of notificaciones) {
        const cookieName = 'notificacionVista_' + popup.id;
        const yaVista = !!getCookie(cookieName);

        if ((popup.portada_id === null || popup.portada_id === undefined) && !yaVista) {
            console.log('Mostrando notificación global con prioridad:', popup.id);
            mostrarPopup(popup, cookieName);
            return;
        }
    }

    //  Si no hay global, continuar con notificaciones específicas
    function pathCoincide(portadaId) {
        const normalizados = path.replace(/^\/+/, '');

        switch (parseInt(portadaId)) {
            case 0:
            case 2: return normalizados === '';
            case 3: return normalizados.startsWith('moda');
            case 4: return normalizados.startsWith('deportesytiempolibre');
            case 5: return normalizados.startsWith('hogar');
            case 6: return normalizados.startsWith('electro');
            case 8: return normalizados.startsWith('supermercado');
            //case 8: return normalizados.startsWith('empresa');
            default: return false;
        }
    }

    for (const popup of notificaciones) {
        const cookieName = 'notificacionVista_' + popup.id;
        const yaVista = !!getCookie(cookieName);
        const coincide = pathCoincide(popup.portada_id);

        if (!yaVista && coincide) {
            mostrarPopup(popup, cookieName);
            return;
        }
    }
    // push
    function mostrarPopup(popup, cookieName) {
        document.getElementById('ModalNotificaciones').style.display = 'block';
        document.getElementById('contenedorNotificacion').style.backgroundImage = `url('${popup.imagen.url}')`;
        document.getElementById('contenedorNotificacion').style.display = 'block';
        document.getElementById('tituloNotif').innerText = popup.titulo ?? "";
        document.getElementById('mensajeNotif').innerText = popup.texto ?? "";
        document.getElementById('linkNotif').innerHTML = `
        <div class="font-size-16">
          <a class="button rounded font-size-16 bold mb-0 bgffffff border-color-ffffff color034D8E"
             href="${popup.url}">${popup.texto_btn}</a>
        </div>`;

        const fechaHasta = new Date(popup.fecha_hasta);
        const ahora = new Date();
        const diasRestantes = Math.ceil((fechaHasta - ahora) / (1000 * 60 * 60 * 24));
        if (diasRestantes > 0) {
            setCookie(cookieName, '1', diasRestantes);
        }

        document.getElementById('btnCerrarNotificacion')?.addEventListener('click', function () {
            document.getElementById('ModalNotificaciones').style.display = 'none';
        });
    }
}

(function esperarNotificaciones() {
    if (window.notificacionesPopUp) {
        mostrarPushNotificacion();
    } else {
        setTimeout(esperarNotificaciones, 100);
    }
})();

//contador
(function esperarBannerContador() {
    if (window.notificacionesContador && document.getElementById("bannerNotificacion")) {

        function pathCoincide(portadaId) {
            const path = window.location.pathname.toLowerCase().replace(/\/+$/, '').replace(/^\/+/, '');
            switch (parseInt(portadaId)) {
                case 0:
                case 2: return path === '';
                case 3: return path.startsWith('moda');
                case 4: return path.startsWith('deportesytiempolibre');
                case 5: return path.startsWith('hogar');
                case 6: return path.startsWith('electro');
                case 8: return path.startsWith('supermercado');
                //case 8: return path.startsWith('empresa');
                default: return false;
            }
        }

        const contadoresGlobales = window.notificacionesContador.filter(n =>
            (n.portada_id === null || n.portada_id === undefined) &&
            n.fecha_hasta && new Date(n.fecha_hasta) > new Date()
        );

        let contador = null;

        if (contadoresGlobales.length > 0) {

            contador = contadoresGlobales[0];
        } else {

            contador = window.notificacionesContador.find(n =>
                n.portada_id !== null && n.portada_id !== undefined &&
                pathCoincide(n.portada_id) &&
                n.fecha_hasta && new Date(n.fecha_hasta) > new Date()
            );
        }

        if (!contador) {
            document.getElementById("bannerNotificacion").style.display = 'none';
            return;
        }

        // Mostrar el banner si hay un contador válido
        document.getElementById("bannerNotificacion").style.display = 'block';

        const banner = document.getElementById("bannerNotificacion");
        const data = contador.imagenes;
        const fechaHasta = new Date(contador.fecha_hasta).getTime();

        const imgEl = document.getElementById('contadorImagen');
        if (imgEl) {
            imgEl.src = contador.imagen?.url || '';
            imgEl.alt = contador.titulo || '';
        }

        const textoEl = document.getElementById('contadorTexto');
        if (textoEl) {
            textoEl.innerText = contador.texto || '';
        }

        const btnEl = document.getElementById('contadorBtn');
        if (btnEl) {
            btnEl.href = contador.url || '#';
            btnEl.innerText = contador.texto_btn || 'Comprá Ya!';
        }

        function actualizarFondo() {
            if (!banner || !data) return;
            const isMobile = window.innerWidth <= 768;
            const fondoUrl = isMobile ? data.mobile?.url : data.desktop?.url;
            if (fondoUrl) {
                banner.style.backgroundImage = `url('${fondoUrl}')`;
                banner.style.backgroundSize = 'cover';
                banner.style.backgroundRepeat = 'no-repeat';
                banner.style.backgroundPosition = 'center';
            }
        }

        function agragarCero(num) {
            return num.toString().padStart(2, '0');
        }

        function actualizarContador() {
            let now = new Date().getTime();
            let distance = fechaHasta - now;

            if (distance < 0) return;

            let days = Math.floor(distance / (1000 * 60 * 60 * 24));
            let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            let seconds = Math.floor((distance % (1000 * 60)) / 1000);

            document.getElementById('days').innerText = agragarCero(days);
            document.getElementById('hours').innerText = agragarCero(hours);
            document.getElementById('minutes').innerText = agragarCero(minutes);
            document.getElementById('seconds').innerText = agragarCero(seconds);

            if (days === 0) {
                document.getElementById('days').style.display = 'none';
                document.getElementById('days2').style.display = 'none';
            }

            requestAnimationFrame(actualizarContador);
        }

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function setCookie(name, value, days) {
            const fecha = new Date();
            fecha.setTime(fecha.getTime() + (days * 24 * 60 * 60 * 1000));
            document.cookie = `${name}=${value}; expires=${fecha.toUTCString()}; path=/; SameSite=Lax`;
        }

        const esCarritoBan = getCookie('esCarritoBan');
        if (esCarritoBan == 1) {
            banner.style.display = 'none';
            setCookie('esCarritoBan', '', -1);
        } else {
            banner.style.height = '45px';
        }

        actualizarFondo();
        window.addEventListener('resize', actualizarFondo);
        requestAnimationFrame(actualizarContador);
    } else {
        setTimeout(esperarBannerContador, 100);
    }
})();

// function agregar_al_carrito_01(idArt, card) {
//     $(`#agregar_${idArt}`).addClass("desaparecer");
//     identificadorTiempoDeEspera = setTimeout(() => agregar_al_carrito_02(idArt, card), 301);
// }
// function agregar_al_carrito_02(idArt, card) {
//     $(`#agregar_${idArt}`).hide(0);
//     $(`#agregado_${idArt}`).show(0);
//     $(`#agregado_${idArt}`).addClass("aparecer");

//     card.addClass("agregado");
// }

// function quitar_del_carrito_01() {
//     $("#agregado_01").addClass("desaparecer");
//     identificadorTiempoDeEspera = setTimeout(quitar_del_carrito_02, 301);
// }

// function quitar_del_carrito_02() {
//     $("#agregar_01").show(0);
//     $("#agregado_01").hide(0);
//     $("#agregar_01").removeClass("desaparecer");
//     $("#agregado_01").removeClass("aparecer");
//     $("#agregado_01").removeClass("desaparecer");
//     $("#producto_001").removeClass("agregado");
// }

function abrir_notificacion() {
    $("#ModalNotificaciones .notificaciones").fadeIn(1050);
    $("#ModalNotificaciones .fondo_negro").fadeIn(350);
}

function quitar_del_carrito_01() {
    $("#agregado_01").addClass("desaparecer");
    identificadorTiempoDeEspera = setTimeout(quitar_del_carrito_02, 301);
}

function quitar_del_carrito_02() {
    $("#agregar_01").show(0);
    $("#agregado_01").hide(0);
    $("#agregar_01").removeClass("desaparecer");
    $("#agregado_01").removeClass("aparecer");
    $("#agregado_01").removeClass("desaparecer");
    $("#producto_001").removeClass("agregado");
}

function cerrar_notificacion() {
    $("#ModalNotificaciones .notificaciones").fadeOut(150);
    $("#ModalNotificaciones .fondo_negro").fadeOut(550);
}
