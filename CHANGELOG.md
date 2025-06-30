# 📝 CHANGELOG - Sistema PEI

## ✅ Versión v1.2-produccion
**Fecha de publicación:** 27/06/2025  
**Estado:** Estable en entorno de producción  
**Tag:** `v1.2-produccion`

### 🔧 Cambios principales:
- ✔️ Se implementó historial mensual completo de indicadores (`HistorialAvance`)
- 📌 Registro de:
  - Avance (valor)
  - Observación asociada
  - Archivo de evidencia (adjunto)
  - Fecha y usuario de cada carga
- 📄 Visualización clara por columnas en la vista `ver_historial.html`
- 📤 Archivos de evidencia guardados en: `media/historial_evidencias/`
- 🛠 Migraciones aplicadas limpiamente a la base de datos
- 🔒 Se eliminaron campos obsoletos como `avance_anterior`, `avance_nuevo` del modelo

### 💾 Archivos modificados:
- `planilla/models.py`
- `planilla/views.py`
- `planilla/templates/planilla/ver_historial.html`
- `planilla/migrations/0013_*.py`

### 📌 Observaciones:
- Esta versión reemplaza el antiguo sistema de historial por comparaciones con un enfoque más claro: registro por edición mensual.
- Ideal para trazabilidad, seguimiento de carga por responsable y auditoría.

---

