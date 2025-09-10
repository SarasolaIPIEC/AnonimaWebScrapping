# CONTRIBUTING.md — Guía de contribución

## Estilo de commits
- Seguir [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):
  `tipo(scope): mensaje`.
- Tipos frecuentes: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- Mensajes en **imperativo**, breves y en español.

## Ramas
- Rama base: `work`.
- Crear ramas de trabajo desde `work` con el prefijo:
  - `feat/` para funcionalidades.
  - `fix/` para correcciones.
  - `docs/` para documentación.
- Usar nombres en `kebab-case` y borrar las ramas luego de fusionar.

## Pull requests
- Mantener un alcance acotado por PR.
- Incluir descripción del cambio, motivación y pasos de prueba.
- Ejecutar `pytest` antes de enviar.
- Requerir al menos una revisión de otra persona; incorporar
  retroalimentación antes de fusionar.
- Evitar commits directos a `work` salvo mantenimiento menor documentado.
