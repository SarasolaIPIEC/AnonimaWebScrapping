$(document).ready(function () {
  $(document).foundation();
  if (!getCookie("Id-Sucursal-Super")) {
    $(".Super").hide()
    // document.getElementsByClassName("Super")[0].remove()
  }
})
function mostrar_filtro_categorias() {
  $("#filtros_categorias").slideDown(350);
  $("#btn_mostrar_filtro_categorias").fadeOut(0);
  $("#btn_ocultar_filtro_categorias").fadeIn(0);
}

function ocultar_filtro_categorias() {
  $("#filtros_categorias").slideUp(350);
  $("#btn_mostrar_filtro_categorias").fadeIn(0);
  $("#btn_ocultar_filtro_categorias").fadeOut(0);
}

function mostrar_filtro_marcas() {
  $("#filtros_marcas").slideDown(350);
  $("#btn_mostrar_filtro_marcas").fadeOut(0);
  $("#btn_ocultar_filtro_marcas").fadeIn(0);
}

function ocultar_filtro_marcas() {
  $("#filtros_marcas").slideUp(350);
  $("#btn_mostrar_filtro_marcas").fadeIn(0);
  $("#btn_ocultar_filtro_marcas").fadeOut(0);
}

function mostrar_filtro_entrega() {
  $("#filtros_entrega").slideDown(350);
  $("#btn_mostrar_filtro_entrega").fadeOut(0);
  $("#btn_ocultar_filtro_entrega").fadeIn(0);
}

function ocultar_filtro_entrega() {
  $("#filtros_entrega").slideUp(350);
  $("#btn_mostrar_filtro_entrega").fadeIn(0);
  $("#btn_ocultar_filtro_entrega").fadeOut(0);
}

function mostrar_filtro_precio() {
  $("#filtros_precio").slideDown(350);
  $("#btn_mostrar_filtro_precio").fadeOut(0);
  $("#btn_ocultar_filtro_precio").fadeIn(0);
}

function ocultar_filtro_precio() {
  $("#filtros_precio").slideUp(350);
  $("#btn_mostrar_filtro_precio").fadeIn(0);
  $("#btn_ocultar_filtro_precio").fadeOut(0);
}

function abrir_filtro() {
  $(".filtro").addClass("abierto");
}

function cerrar_filtro() {
  $(".filtro").removeClass("abierto");
}

function mostrar_mas(i) {
  var element = document.getElementById("filtro_" + i);
  element.classList.add("ampliado");
  $("#btn_mostrar_mas_" + i).fadeOut(0);
  $("#btn_mostrar_menos_" + i).fadeIn(200);
}

function mostrar_menos(i) {
  var element = document.getElementById("filtro_" + i);
  element.classList.remove("ampliado");
  $("#btn_mostrar_mas_" + i).fadeIn(200);
  $("#btn_mostrar_menos_" + i).fadeOut(0);
}

/* Agregar */
function agregar_al_carrito_01(idArt, card) {
  document.querySelectorAll(`#agregar_${idArt}`).forEach((agregadoBtn) => {
    agregadoBtn.classList.add("desaparecer");
  })

  identificadorTiempoDeEspera = setTimeout(() => agregar_al_carrito_02(idArt, card), 301);
}
function agregar_al_carrito_02(idArt, card) {
  document.querySelectorAll(`#agregar_${idArt}`).forEach((agregadoBtn) => {
    $(agregadoBtn).hide(0);
  })
  document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
    $(agregadoBtn).show(0);
    agregadoBtn.classList.add("aparecer");
  })
  if (!/^\/[^\/]+\/art_\d+/.test(location.pathname)) {
    document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
      agregadoBtn.closest('.card').classList.add("agregado");
    })
  } else {
    $(`.btnSelecta${idArt}`).hide(0);
  }
}

/* Quitar */
function quitar_del_carrito_01(card, idArt) {
  document.querySelectorAll(`#agregar_${idArt}`).forEach((agregadoBtn) => {
    agregadoBtn.classList.remove("desaparecer");
  })
  identificadorTiempoDeEspera = setTimeout(() => quitar_del_carrito_02(idArt, card), 301);
}

function quitar_del_carrito_02(idArt, card) {
  document.querySelectorAll(`#agregar_${idArt}`).forEach((agregadoBtn) => {
    $(agregadoBtn).show(0);
  })
  document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
    agregadoBtn.classList.remove("aparecer");
    $(agregadoBtn).hide(0);

  })
  if (!/^\/[^\/]+\/art_\d+/.test(location.pathname)) {
    document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
      agregadoBtn.closest('.card').classList.remove("agregado");
    })
  } else {
    $(`.btnSelecta${idArt}`).show(0);
  }
}




function abrir_notificacion() {
  $("#ModalNotificaciones .notificaciones").fadeIn(1050);
  $("#ModalNotificaciones .fondo_negro").fadeIn(350);
}

function cerrar_notificacion() {
  $("#ModalNotificaciones .notificaciones").fadeOut(150);
  $("#ModalNotificaciones .fondo_negro").fadeOut(550);
}



function abrir_doblecarrito() {
  $("#doblecarrito .modal").fadeIn(1050);
  $("#doblecarrito .fondo_negro").fadeIn(350);
}

function cerrar_doblecarrito() {
  $("#doblecarrito .modal").fadeOut(150);
  $("#doblecarrito .fondo_negro").fadeOut(550);
}

function mostrar_menu_b_c() {
  $("#menu_b").slideDown(350);
  $("#menu_c").slideDown(350);
  $("#btn_mostrar_menu_b_c").slideUp(0);
  $("#btn_colapsar_menu_b_c").slideDown(0);
}

function colapsar_menu_b_c() {
  $("#menu_b").slideUp(350);
  $("#menu_c").slideUp(350);
  $("#btn_mostrar_menu_b_c").slideDown(0);
  $("#btn_colapsar_menu_b_c").slideUp(0);
}

function mostrar_menu_d() {
  $("#menu_d").slideDown(350);
  $("#btn_mostrar_menu_d").slideUp(0);
  $("#btn_colapsar_menu_d").slideDown(0);
}

function colapsar_menu_d() {
  $("#menu_d").slideUp(350);
  $("#btn_mostrar_menu_d").slideDown(0);
  $("#btn_colapsar_menu_d").slideUp(0);
}


if (typeof $.fn.slick === 'undefined') {
  loadStyle(DOMINIO_WEB_UNIFICACION + '/css/slick.css');
  loadStyle(DOMINIO_WEB_UNIFICACION + '/css/slick-theme.css');
  loadScript(DOMINIO_WEB_UNIFICACION + '/js/slick.js', function () { });
}

function loadScript(url, callback) {
  var script = document.createElement('script');
  script.src = url;
  script.onload = callback;
  document.head.appendChild(script);
}

function loadStyle(url) {
  var link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = url;
  document.head.appendChild(link);
}


// Initialize slick with a small delay to ensure DOM is completely ready
setTimeout(function () {

  $(".slide-a").slick({
    dots: true,
    infinite: true,
    slidesToShow: 1,
    slidesToScroll: 1,
    speed: 1000,
    autoplay: true,
    autoplaySpeed: 3000,
  });

  $(".slide-a-mobile").slick({
    dots: false,
    infinite: true,
    slidesToShow: 1,
    slidesToScroll: 1,
    speed: 1000,
    autoplay: true,
    autoplaySpeed: 3000,
    arrows: false,
    centerMode: true,
    responsive: [
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
          centerMode: false,
        }
      }
    ]
  });


  $(document).on('ready', function () {
    $(".slide-zocalo-mobile").slick({
      dots: false,
      infinite: true,
      slidesToShow: 1,
      slidesToScroll: 1,
      speed: 1000,
      autoplay: true,
      autoplaySpeed: 3000,
      arrows: false,

    });
  });



  $(document).on('ready', function () {
    $(".menu-a").slick({
      dots: false,
      infinite: false,
      slidesToShow: 6,
      slidesToScroll: 6,
      speed: 1000,
      autoplay: false,
      autoplaySpeed: 3000,

    });
  });




  $(".menu-a-mobile").slick({
    dots: false,
    infinite: true,
    speed: 1000,
    variableWidth: true,
    arrows: false,

  });


  $(".zona-banner").slick({
    dots: true,
    arrows: false,
    infinite: false,
    speed: 600,
    slidesToShow: 5,
    slidesToScroll: 5,
    variableWidth: true,
    responsive: [
      {
        breakpoint: 1210,
        settings: {
          slidesToShow: 4.5,
          slidesToScroll: 4,
        }
      },
      {
        breakpoint: 1210,
        settings: {
          slidesToShow: 3.5,
          slidesToScroll: 3,

        }
      },
      {
        breakpoint: 900,
        settings: {
          slidesToShow: 2.5,
          slidesToScroll: 2,
        }
      },
      {
        breakpoint: 640,
        settings: {
          slidesToShow: 2.5,
          slidesToScroll: 2,
        }
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1.5,
          slidesToScroll: 1,
        }
      }
    ]
  });



  $(document).on('ready', function () {
    $(".zona-banner-variable").slick({
      dots: true,
      infinite: true,
      speed: 300,
      slidesToShow: 5,
      slidesToScroll: 5,
      variableWidth: true
    });
  });



  $(document).on('ready', function () {
    $(".zona-banner-6").slick({
      dots: true,
      infinite: false,
      slidesToShow: 6,
      slidesToScroll: 6,
      speed: 1000,
      autoplay: true,
      autoplaySpeed: 3000,
      responsive: [
        {
          breakpoint: 1210,
          settings: {
            slidesToShow: 6,
            slidesToScroll: 6,

          }
        },
        {
          breakpoint: 1024,
          settings: {
            slidesToShow: 4,
            slidesToScroll: 4,

          }
        },
        {
          breakpoint: 900,
          settings: {
            slidesToShow: 6,
            slidesToScroll: 6,
          }
        },
        {
          breakpoint: 640,
          settings: {
            dots: false,
            slidesToShow: 3,
            slidesToScroll: 3,
            arrows: false,
            speed: 1000,
            autoplay: false,
            autoplaySpeed: 3000,
          }
        },
        {
          breakpoint: 480,
          settings: {
            dots: false,
            slidesToShow: 2,
            slidesToScroll: 2,
            arrows: false,
            speed: 1000,
            autoplay: false,
            autoplaySpeed: 3000,
          }
        }
      ]
    });
  });




  $(".slide-destacado").slick({
    dots: false,
    infinite: false,
    slidesToShow: 5,
    slidesToScroll: 5,
    speed: 1000,
    autoplay: false,
    autoplaySpeed: 3000,
    arrows: false,
    responsive: [
      {
        breakpoint: 1210,
        settings: {
          slidesToShow: 4.5,
          slidesToScroll: 4,

        }
      },
      {
        breakpoint: 1110,
        settings: {
          slidesToShow: 4.2,
          slidesToScroll: 4,

        }
      },
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 3.5,
          slidesToScroll: 3,

        }
      },
      {
        breakpoint: 900,
        settings: {
          slidesToShow: 3.2,
          slidesToScroll: 2,
        }
      },
      {
        breakpoint: 780,
        settings: {
          slidesToShow: 2.6,
          slidesToScroll: 1,
          arrows: false,
        }
      },
      {
        breakpoint: 640,
        settings: {
          slidesToShow: 2.2,
          slidesToScroll: 1,
          arrows: false,
        }
      },
      {
        breakpoint: 540,
        settings: {
          slidesToShow: 1.8,
          slidesToScroll: 1,
          arrows: false,
        }
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 1.5,
          slidesToScroll: 1,
          arrows: false,
        }
      },
      {
        breakpoint: 355,
        settings: {
          slidesToShow: 1.2,
          slidesToScroll: 1,
          arrows: false,
        }
      }
    ]
  });



  $(".iconos_activos").slick({
    dots: true,
    infinite: false,
    slidesToShow: 8,
    slidesToScroll: 4,
    speed: 1000,
    autoplay: false,
    autoplaySpeed: 3000,
    arrows: true,
    responsive: [
      {
        breakpoint: 1210,
        settings: {
          slidesToShow: 7.5,

        }
      },
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 6.5,

        }
      },
      {
        breakpoint: 900,
        settings: {
          slidesToShow: 5.5,
        }
      },
      {
        breakpoint: 640,
        settings: {
          slidesToShow: 4.5,
          arrows: false,
        }
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 3.5,
          slidesToScroll: 3,
          arrows: false,
        }
      }
    ]
  });




  $(".carusel").slick({
    dots: true,
    infinite: false,
    slidesToShow: 4,
    slidesToScroll: 4,
    speed: 1000,
    autoplay: false,
    autoplaySpeed: 3000,
    arrows: true,
    responsive: [
      {
        breakpoint: 1210,
        settings: {
          slidesToShow: 4,
          slidesToScroll: 3,

        }
      },
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 3,
          slidesToScroll: 3,
        }
      },
      {
        breakpoint: 960,
        settings: {
          slidesToShow: 3,
          slidesToScroll: 3,
        }
      },
      {
        breakpoint: 640,
        settings: {
          slidesToShow: 2,
          arrows: false,
          slidesToScroll: 2,
        }
      },
      {
        breakpoint: 480,
        settings: {
          slidesToShow: 2,
          arrows: false,
          slidesToScroll: 2,
        }
      },
      {
        breakpoint: 360,
        settings: {
          slidesToShow: 1,
          arrows: false,
          slidesToScroll: 1,
        }
      }

    ]
  });

}, 200);


/* agregar cal carrito en portadas y busqueda */
$(document).on("click", ".btnAgregarCarritoVarios", function (event) {
  // $(".btnAgregarCarritoVarios").on("click", function () {
  const $card = $(this).closest('.card');
  const button = $(this).find("button");
  const existenciaSuper = button.data('existencia-super');

  if (getCookie("es_empleado_v1") || getCookie("es_empleado")) {
  } else {
    let puede = existenciaSuper === 'N' && getCookie("codigoPostal") == "HB018305";
    if (getCookie("tipoEnvioUnificado") == 0 || puede) {
      var modal = new Foundation.Reveal($('#codigo-postal'));
      modal.open();
      setTimeout(() => {
        const visible = $('#codigo-postal').is(':visible') && $('#codigo-postal').outerHeight() > 0 && $('#codigo-postal').css('display') !== 'none';
        if (!visible) {
          alert("No se pudo abrir un pop-up. Posiblemente el navegador o la red lo esté bloqueando. Revisá tu configuración e intentá nuevamente.");
        }
      }, 1000);
      return
    }
  }

  const codAnonima = button.data('cod-anonima');
  const idArt = button.data('idarticulo');
  const step = button.data('step');



  const endpoint = existenciaSuper === 'S' ? '/carrito/super/articulo/' : '/carrito/articulo/';

  fetch(endpoint + codAnonima, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      cantidad: step,
    }),
  })
    .then(response => {

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (data.success && (data.data.statusCode === 200 || data.data.statusCode === 201)) {
        if (data['data']['data'].idEcmsCarrito) {
          document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
            agregadoBtn.querySelector('.input-group-label.mas').setAttribute('data-codigo', data['data']['data'].idEcmsCarrito);
            agregadoBtn.querySelector('.input-group-label.menos').setAttribute('data-codigo', data['data']['data'].idEcmsCarrito);
            $(agregadoBtn).closest('.card').find('.input-group-field').val(step);
          })
          // agregar_2431476
          // $(this).closest('.card').find('.input-group-label.menos').attr('data-codigo', data['data']['data'].idEcmsCarrito);
          // $(this).closest('.card').find('.input-group-label.mas').attr('data-codigo', data['data']['data'].idEcmsCarrito);
          $('.electro').show();

        }

        if (data['data']['data'].id) {
          document.querySelectorAll(`#agregado_${idArt}`).forEach((agregadoBtn) => {
            agregadoBtn.querySelector('.input-group-label.mas').setAttribute('data-codigo', data['data']['data'].id);
            agregadoBtn.querySelector('.input-group-label.menos').setAttribute('data-codigo', data['data']['data'].id);
            $(agregadoBtn).closest('.card').find('.input-group-field').val(step);
          })
          $('.menu.carrito .supermercado').show();

          if ($('.electro.is-submenu-item.is-dropdown-submenu-item').css('display') === 'none') {
            $("#linkCarrito").attr("href", `${DOMINIO_WEB_UNIFICACION}/carrito#supermercado`);
          }
        }

        // document.querySelector(".menu.carrito.submenu").style.display = ""


        showMessage('success', 'Producto agregado al carrito correctamente');
        $("#total_carrito").text(+$("#total_carrito").text() + 1);
        // $(this).closest('.card').find('#div-btn-editar-cantidad').show()
        // $(this).closest('.card').find('#div-btn-agregar-carrito').hide()
        agregar_al_carrito_01(idArt, $(this).closest('.card'))
        if (existenciaSuper === 'S') {
          $("#linkCarrito").attr("href", `${DOMINIO_WEB_UNIFICACION}/carrito#supermercado`);
        } else {
          $("#linkCarrito").attr("href", `${DOMINIO_WEB_UNIFICACION}/carrito`);
        }
        if (button && EventCapturer.eventsToCart) {
          EventCapturer.eventsToCart(event, 'addToCart', existenciaSuper)
        }

      } else if (data.data && data.data.error) {
        // Handle error response with nested structure
        showMessage('error', data.data.error.description);
      } else {
        throw new Error(data.error || 'Error al agregar al carrito');
      }
    })
    .catch(error => {
      showMessage('error', error.message || 'Error al agregar al carrito');
      console.error('Error:', error);
    });
})

// /* editar cantidad portadas y busquedas */
$(document).on("click", ".input-group-label", function (event) {
  let codigoProducto = this.getAttribute("data-codigo");
  let accion = this.getAttribute("data-accion");
  let codtener = this.getAttribute("data-codtener");
  const existenciaSuper = this.getAttribute('data-existencia-super');

  let input = $(this).closest(".input-group").find(".input-group-field");
  let step = Number(input.attr("step")) || 1;

  let cantidadActual = Number(input.val());
  if (accion === "plus") { cantidadActual += step; }
  if (accion === "minus") { cantidadActual -= step; }


  if (cantidadActual == 0 || cantidadActual <= 0) {
    borrarProducto(codigoProducto, existenciaSuper, $(this).closest('.card'), codtener, event);
    return;
  }

  const endpoint = existenciaSuper === 'S' ? '/carrito/super/articulo/cantidadArticulos' : '/carrito/cantidadArticulos';
  fetch(endpoint + "/" + codigoProducto, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      cantidad: cantidadActual,
    })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (data.success && data.data.statusCode == 200) {
        if (+$("#total_carrito").text() != 0) {
          $("#total_carrito").text(+$("#total_carrito").text() - 1);
        }
        document.querySelectorAll(`#agregado_${codtener}`).forEach((div) => {
          const input = div.querySelector("input");
          $(input).val(cantidadActual);
        })

        showMessage('success', data.data.data);
        if (window.location.pathname == '/carrito') {
          setTimeout(() => {
            if (existenciaSuper === 'S' && data.data.statusCode == 200) {
              window.location.reload();
            } else {

              window.location.href = data.data.redirectUrl;
            }
          }, 3000);
        }
        if (EventCapturer) {
          let tipoCarrito = accion === "plus" ? "addToCart" : "removeToCart";
          EventCapturer.eventsToCart(event, tipoCarrito, existenciaSuper);
        }
      } else {
        // throw new Error(data.error || 'Error al actualizar producto del carrito');
        showMessage('error', data.data.error.description || 'Error al actualizar producto del carrito');
      }
    })
    .catch(error => {
      showMessage('error', error || 'Error al actualizar producto del carrito');
    });

})

$("#btn_favorito").on("click", function () {
  let dataCodigo = this.getAttribute('data-codigo');
  let esSuper = this.getAttribute('data-super');

  const endpoint = esSuper == 'S' ? 'agregarFavorito/super?idProducto=' + dataCodigo + '&cantidad=' + this.getAttribute('data-cantidad') : 'agregarFavorito?idProducto=' + dataCodigo;

  if (!$(this).hasClass('fav_activo')) {
    $.ajax({
      url: "/ajax/" + endpoint,
      type: 'GET',
      dataType: 'json',
      crossDomain: true,
      xhrFields: {
        withCredentials: true  // NECESARIO para que se envíen cookies a subdominios
      },
      success: function (response) {
        if (response?.statusCode == 401) {
          let modal = new Foundation.Reveal($('#modal-no-logueado'));
          modal.open();
        } else if (response?.statusCode != 500) {
          $(`#btn_favorito`).addClass("fav_activo")
          if (EventCapturer) {
            EventCapturer.eventToFavorite('favoritein', esSuper);
          }
        }
      },
      error: function (error) {
        console.error('Error al agregar a favoritos:', error);
      }
    });
  } else {

    const endpointDelete = esSuper == 'S' ? 'borrarFavorito/super' : 'borrarFavorito';

    $.ajax({
      url: "/ajax/" + endpointDelete + "?idProducto=" + dataCodigo,
      type: 'DELETE',
      dataType: 'json',
      crossDomain: true,
      xhrFields: {
        withCredentials: true  // NECESARIO para que se envíen cookies a subdominios
      },
      success: function (response) {
        if (response?.statusCode == 401) {
          let modal = new Foundation.Reveal($('#modal-no-logueado'));
          modal.open();
        } else if (response?.statusCode != 500) {
          $(`#btn_favorito`).removeClass("fav_activo")
          if (esSuper != 'S') {
            EventCapturer.eventToFavorite('favoriteout');
          }
        }
      },
      error: function (error) {
        console.error('Error al agregar a favoritos:', error);
      }
    });
  }

})


// Function to show messages
function showMessage(type, message) {
  let messageContainer = document.getElementById('cart-message');

  // Create message container if it doesn't exist
  if (!messageContainer) {
    messageContainer = document.createElement('div');
    messageContainer.id = 'cart-message';
    document.body.appendChild(messageContainer);
  }

  messageContainer.textContent = message;
  messageContainer.className = 'cart-message ' + type;
  messageContainer.style.display = 'block';

  setTimeout(function () {
    messageContainer.style.display = 'none';
  }, 500);
}

function borrarProducto(id, existenciaSuper, card, valor, event) {
  // let id = $(this).data("id");
  // let existenciaSuper = $(this).data("existencia-super");

  const endpoint = existenciaSuper === 'S' ? '/carrito/eliminarArticuloSuper' : '/carrito/eliminarArticulo';
  fetch(endpoint + "/" + id, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (data.success && data.redirectUrl) {
        if (window.location.pathname == '/carrito') {
          showMessage('success', data.message);
          setTimeout(() => {
            if (existenciaSuper === 'S') {
              window.location.href = data.redirectUrl;
              setTimeout(() => {
                window.location.reload();
              }, 50);
            } else {
              window.location.href = data.redirectUrl;
            }
          }, 3000);
        } else {
          quitar_del_carrito_01(card, valor)
          card.find('.input-group-label.menos').attr('data-codigo', valor);
          card.find('.input-group-label.mas').attr('data-codigo', valor);
        }

        if (EventCapturer) {
          let tipoCarrito = "removeToCart";
          EventCapturer.eventsToCart(event, tipoCarrito, existenciaSuper);
        }

      } else {
        throw new Error(data.error || 'Error al borrar producto del carrito');
      }
    })
    .catch(error => {
      showMessage('error', error.message || 'Error al borrar producto del  carrito');
      console.error('Error:', error);
    });
}


function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}


function cargarFechasContador() {
  try {
    for (const item of document.querySelectorAll('[fecha_contador]')) {
      const fecha = new Date(item.getAttribute('fecha_contador'))
      if (fecha) {
        item._interval_fecha_contador = setInterval(() => {
          var now = new Date().getTime();
          const fecha_i = fecha.getTime()

          var distance = fecha_i - now;

          var days = Math.floor(distance / (1000 * 60 * 60 * 24));
          var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
          var seconds = Math.floor((distance % (1000 * 60)) / 1000);

          var hours0 = String(hours).padStart(2, '0');
          var minutes0 = String(minutes).padStart(2, '0');
          var seconds0 = String(seconds).padStart(2, '0');

          var hours01 = hours0.toString()[0];
          var hours02 = hours0.toString()[1];
          var minutes01 = minutes0.toString()[0];
          var minutes02 = minutes0.toString()[1];
          var seconds01 = seconds0.toString()[0];
          var seconds02 = seconds0.toString()[1];

          let dias_text = ''
          if (days && days > 0) {
            if (days == 1) dias_text = "<span>" + days + " d&iacute;a </span>"
            else dias_text = "<span>" + days + " d&iacute;as </span>"
          }

          item.innerHTML = "<div>" + dias_text + "<span>" + hours01 + "</span><span>" + hours02 + "</span>:<span>" + minutes01 + "</span><span>" + minutes02 + "</span>:<span>" + seconds01 + "</span><span>" + seconds02 + "</span></div>";

          if (distance < 1) {
            clearInterval(item._interval_fecha_contador);
            item.innerHTML = ''
          }

        }, 1000);
      }
    }
  }
  catch (er) {
    console.error(er)
  }
}