# limpiar_tablero.py

import os
import django
import logging
from datetime import datetime

# Configurar entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard_project.settings")
django.setup()

from planilla.models import Tablero, HistorialAvance

# Configurar logging
log_dir = '/var/log/dashboard'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'limpieza_tablero.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

def limpiar_tablero():
    logging.info("🧼 Inicio del proceso de limpieza del tablero.")

    # Limpiar campos del modelo Tablero
    try:
        Tablero.objects.all().update(
            avance='',
            nivel='',
            accion='',
            observacion='',
            evidencia=None
        )
        logging.info("✔️ Campos 'avance', 'nivel', 'acción', 'observación' y 'evidencia' limpiados.")
    except Exception as e:
        logging.error(f"❌ Error al limpiar campos del tablero: {str(e)}")

    # Eliminar historial
    try:
        cantidad = HistorialAvance.objects.count()
        HistorialAvance.objects.all().delete()
        logging.info(f"🗑️ Se eliminaron {cantidad} registros del historial de avances.")
    except Exception as e:
        logging.error(f"❌ Error al eliminar historial: {str(e)}")

    logging.info("✅ Proceso de limpieza finalizado.")

if __name__ == "__main__":
    limpiar_tablero()
