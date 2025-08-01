#!/bin/bash

# 🗓️ Fecha y hora actual
FECHA=$(date +%F_%H-%M)
DESTINO="/opt/backups"
PROYECTO_DIR="/opt/dashboard_project"
ARCHIVOS_DIR="/opt/dashboard_project/media"
BD_NOMBRE="dashboard"
USUARIO_BD="djangouser"

# 🔐 Contraseña para postgres (usa variable de entorno o .pgpass si querés evitar el prompt)
export PGPASSWORD="uid2025"

# 📁 Crear carpeta de respaldo si no existe
mkdir -p "$DESTINO"

echo "🔄 Iniciando respaldo PEI - $FECHA"

# 📦 1. Respaldar código fuente
echo "📁 Respaldando código fuente..."
tar -czf "$DESTINO/codigo_pei_$FECHA.tar.gz" -C "$PROYECTO_DIR" .

# 🗃️ 2. Respaldar base de datos PostgreSQL
echo "🗃️ Respaldando base de datos..."
pg_dump -U "$USUARIO_BD" -h localhost "$BD_NOMBRE" > "$DESTINO/db_pei_$FECHA.sql"
gzip "$DESTINO/db_pei_$FECHA.sql"

# 📎 3. Respaldar archivos subidos (evidencias)
echo "📂 Respaldando archivos subidos..."
tar -czf "$DESTINO/evidencias_pei_$FECHA.tar.gz" -C "$ARCHIVOS_DIR" .

# 🧹 4. Eliminar respaldos de más de 15 días
echo "🧹 Eliminando respaldos antiguos (15+ días)..."
find "$DESTINO" -type f -mtime +15 -name "*.tar.gz" -exec rm -f {} \;
find "$DESTINO" -type f -mtime +15 -name "*.sql.gz" -exec rm -f {} \;

echo "✅ Respaldo completo realizado en: $DESTINO"

# 🧽 Limpiar variable sensible
unset PGPASSWORD

# 📝 Registrar en log
echo "$(date '+%F %T') - Backup completado exitosamente" >> /var/log/respaldo_pei.log