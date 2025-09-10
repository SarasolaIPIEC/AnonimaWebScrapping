
# FAQ.md — Preguntas frecuentes

**¿Por qué usar La Anónima Online?**
Porque refleja precios locales de Ushuaia y permite observación sistemática.

**¿Puedo usar precios de otras sucursales?**
El flujo está pensado para la sucursal de Ushuaia. Se puede cambiar la sucursal en la [configuración](../README.md#configuración) antes de ejecutar el scraping. El paso inicial del [runbook](./RUNBOOK.md#flujo-general) también recuerda verificar la sucursal activa.

**¿Qué pasa si un producto no aparece o está sin stock?**
Se aplica **sustitución documentada** siguiendo reglas previamente definidas. Ver [metodología](./METHODOLOGY.md#canasta-básica-alimentaria-cba) y las [validaciones del runbook](./RUNBOOK.md#validaciones-mínimas-por-corrida).

**¿Se usan precios con promoción?**
Sí, si la promoción representa el **precio final** que paga el consumidor en Ushuaia. Detalles en [precio relevante](./METHODOLOGY.md#precio-relevante).

**¿En qué se diferencia del IPC Patagonia?**
Nuestro índice usa una canasta fija local y precios finales de Ushuaia, mientras que el IPC Patagonia es regional y oficial. Consulta la [introducción del README](../README.md#ipc-ushuaia--documentación-guía-solo-textos) y la [metodología](./METHODOLOGY.md#canasta-básica-alimentaria-cba) para comprender el enfoque específico.

**¿La canasta cambia con el tiempo?**
No. Es **fija** para medir variaciones de precios; cualquier ajuste se documenta como cambio metodológico.

**¿Cómo se interpreta el índice base=100?**
El valor 100 corresponde al costo de la canasta en el primer período de la serie. Los valores posteriores indican variaciones relativas.
