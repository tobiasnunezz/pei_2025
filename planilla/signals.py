from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        from .models import PerfilUsuario  # Importar aquí dentro de la función
        PerfilUsuario.objects.create(user=instance)
