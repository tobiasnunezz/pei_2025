from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from crum import get_current_user
from .models import PerfilUsuario, Tablero, HistorialCambio
import logging

logger = logging.getLogger(__name__)  # logger configurado en settings.py

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
