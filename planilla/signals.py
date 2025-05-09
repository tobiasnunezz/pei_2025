from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Tablero, HistorialCambio

# 🔧 Crear automáticamente perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

# 📜 Registrar historial de cambios antes de guardar el tablero
@receiver(pre_save, sender=Tablero)
def registrar_cambios(sender, instance, **kwargs):
    if not instance.pk:
        return  # Si es nuevo, no comparamos

    try:
        original = Tablero.objects.get(pk=instance.pk)
    except Tablero.DoesNotExist:
        return

    campos = ['avance', 'nivel', 'accion']
    for campo in campos:
        valor_anterior = getattr(original, campo)
        valor_nuevo = getattr(instance, campo)

        if valor_anterior != valor_nuevo:
            usuario = getattr(instance, '_usuario_modificando', None)
            if usuario:
                HistorialCambio.objects.create(
                    tablero=instance,
                    usuario=usuario,
                    campo_modificado=campo,
                    valor_anterior=valor_anterior,
                    valor_nuevo=valor_nuevo
                )

