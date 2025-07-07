# cargar_usuarios.py

import os
import django
import csv
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from django.contrib.auth.models import User
from planilla.models import PerfilUsuario

# Configurar logging
log_path = '/var/log/dashboard/carga_usuarios.log'
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(message)s')

def crear_usuarios_desde_csv(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row['username'].strip()
            nombre = row['nombre'].strip()
            email = row['email'].strip()
            password = row['password'].strip()
            responsable = row['responsable'].strip()

            if User.objects.filter(username=username).exists():
                logging.warning(f"⚠️ Usuario {username} ya existe. Se omite.")
                continue

            try:
                user = User.objects.create_user(
                    username=username,
                    first_name=nombre,
                    email=email,
                    password=password
                )
                PerfilUsuario.objects.create(usuario=user, responsable=responsable)
                logging.info(f"✅ Usuario {username} creado exitosamente.")
            except Exception as e:
                logging.error(f"❌ Error al crear usuario {username}: {str(e)}")

if __name__ == '__main__':
    crear_usuarios_desde_csv('/opt/dashboard_project/usuarios_nuevos.csv')
    print("✅ Proceso de carga finalizado. Ver log en /var/log/dashboard/carga_usuarios.log")
