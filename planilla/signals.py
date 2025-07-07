from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from crum import get_current_user
from .models import PerfilUsuario, Tablero, HistorialCambio, BitacoraAcceso
from django.utils.timezone import now
import logging

# Log principal del sistema
logger = logging.getLogger(__name__)

# Log exclusivo de accesos (definido en settings.py)
logger_accesos = logging.getLogger('accesos')

# 🔧 Crea perfil automáticamente cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
        logger.info(f"✅ Perfil creado para el nuevo usuario: {instance.username}")

# 📜 Registra cambios automáticamente antes de guardar Tablero
@receiver(pre_save, sender=Tablero)
def registrar_cambios(sender, instance, **kwargs):
    if not instance.pk:
        return  # No registra si es un nuevo objeto

    try:
        original = Tablero.objects.get(pk=instance.pk)
    except Tablero.DoesNotExist:
        return

    usuario = get_current_user()
    if not usuario or not usuario.is_authenticated:
        logger.warning("❌ Usuario no autenticado, no se registrará historial")
        return

    campos = ['avance', 'nivel', 'accion']
    for campo in campos:
        anterior = getattr(original, campo)
        nuevo = getattr(instance, campo)
        if anterior != nuevo:
            HistorialCambio.objects.create(
                usuario=usuario,
                indicador=instance,
                campo=campo,
                valor_anterior=anterior or '',
                valor_nuevo=nuevo or ''
            )
            logger.info(f"📝 Cambio registrado por {usuario.username}: {campo} -> '{anterior}' a '{nuevo}'")

# 🛂 Registrar login y logout
@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    logger_accesos.info(f"Usuario '{user.username}' inició sesión desde IP {ip} a las {now()}")
    BitacoraAcceso.objects.create(usuario=user, ip=ip, accion='login')

@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    if user.is_authenticated:
        BitacoraAcceso.objects.create(usuario=user, ip=ip, accion='logout')
