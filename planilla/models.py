from django.db import models
from django.contrib.auth.models import User
import re  # Necesario para limpiar valores numéricos
from django.utils import timezone

# Tipos de meta posibles
TIPO_META_CHOICES = [
    ('porcentaje', 'Porcentaje'),
    ('numero', 'Número'),
    ('texto', 'Texto'),
]

class Tablero(models.Model):
    eje_estrategico = models.CharField(max_length=255)
    objetivo_estrategico = models.TextField()
    indicador = models.TextField()
    meta_2025 = models.CharField(max_length=100)
    tipo_meta = models.CharField(
        max_length=20,
        choices=TIPO_META_CHOICES,
        default='porcentaje'
    )
    avance = models.CharField(max_length=100, blank=True, null=True)
    nivel = models.CharField(max_length=50, blank=True)
    accion = models.CharField(max_length=50, blank=True)
    responsable = models.CharField(max_length=100, blank=True)
    orden = models.PositiveIntegerField(default=0)
    observacion = models.TextField(blank=True, null=True)
    #evidencia = models.FileField(upload_to='evidencias/', blank=True, null=True)

    def calcular_nivel_y_accion(self):
        avance_raw = self.avance
        avance = str(avance_raw).strip().lower() if isinstance(avance_raw, str) else avance_raw
        tipo_meta = self.tipo_meta

        try:
            avance_val = float(str(avance).replace(',', '.'))

            if tipo_meta == 'porcentaje':
                if avance_val == 0:
                    self.nivel = "No existe avance"
                    self.accion = "Correctiva"
                elif avance_val < 25:
                    self.nivel = "Bajo"
                    self.accion = "Correctiva"
                elif avance_val < 50:
                    self.nivel = "Aceptable"
                    self.accion = "Preventiva"
                elif avance_val < 75:
                    self.nivel = "Medio"
                    self.accion = "Preventiva"
                elif avance_val < 90:
                    self.nivel = "Satisfactorio"
                    self.accion = "Analizar tendencias"
                else:
                    self.nivel = "Óptimo"
                    self.accion = "Analizar tendencias"

            elif tipo_meta == 'numero':
                meta_limpia = re.sub(r'[^\d.,]', '', self.meta_2025 or '').replace(',', '.')
                try:
                    meta_val = float(meta_limpia)
                    if meta_val > 0:
                        porcentaje = (avance_val / meta_val) * 100
                        if porcentaje == 0:
                            self.nivel = "No existe avance"
                            self.accion = "Correctiva"
                        elif porcentaje < 50:
                            self.nivel = "Bajo"
                            self.accion = "Correctiva"
                        elif 50 <= porcentaje < 100:
                            self.nivel = "Medio"
                            self.accion = "Preventiva"
                        elif porcentaje == 100:
                            self.nivel = "Óptimo"
                            self.accion = "Analizar tendencias"
                        else:
                            self.nivel = "Satisfactorio"
                            self.accion = "Analizar tendencias"
                    else:
                        self.nivel = ""
                        self.accion = ""
                except ValueError:
                    self.nivel = ""
                    self.accion = ""

        except ValueError:
            if isinstance(avance, str) and avance in ["no iniciado"]:
                self.nivel = "No existe avance"
                self.accion = "Correctiva"
            elif isinstance(avance, str) and avance in ["en proceso"]:
                self.nivel = "Medio"
                self.accion = "Preventiva"
            elif isinstance(avance, str) and avance in ["aprobado", "presentado", "aprobada", "presentada"]:
                self.nivel = "Óptimo"
                self.accion = "Analizar tendencias"
            else:
                self.nivel = ""
                self.accion = ""

    class Meta:
        ordering = ['orden']


class PerfilUsuario(models.Model):
    class RolChoices(models.TextChoices):
        EDITOR = "editor", "Editor"
        LECTOR = "lector", "Lector"
        ADMIN  = "admin",  "Admin"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    responsable = models.CharField(max_length=100)

    # ← NUEVO: opcional para poder crear el usuario sin romper
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        null=True, blank=True
    )
    def __str__(self):
        return f"{self.user.username} - {self.responsable}"


class HistorialCambio(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    indicador = models.ForeignKey(Tablero, on_delete=models.CASCADE)
    campo = models.CharField(max_length=100)
    valor_anterior = models.CharField(max_length=255, blank=True, null=True)
    valor_nuevo = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} cambió {self.campo} en '{self.indicador.indicador}'"


class HistorialAvance(models.Model):
    tablero = models.ForeignKey('Tablero', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    avance = models.CharField(max_length=255, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    #evidencia = models.FileField(upload_to='historial_evidencias/', blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tablero.indicador} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

class Evidencia(models.Model):
    """
    Modelo para almacenar cada archivo de evidencia asociado a un registro
    de historial de avance.
    """
    historial_avance = models.ForeignKey(HistorialAvance, related_name='evidencias', on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='evidencias/')

    def __str__(self):
        # Devuelve el nombre del archivo para una mejor representación en el admin
        return self.archivo.name

class EvidenciaHistorica(models.Model):
    """
    Modelo para la evidencia 'histórica' o 'permanente'.
    Estos archivos se guardan en /media/historial_evidencias/ y NO se eliminan.
    """
    historial_avance = models.ForeignKey(HistorialAvance, related_name='evidencias_historicas', on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='historial_evidencias/')
    nombre_original = models.CharField(max_length=255, help_text="Nombre del archivo original subido por el usuario")

    def __str__(self):
        return self.nombre_original

class BitacoraAcceso(models.Model):
    ACCION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('password_change', 'Cambio de contraseña'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()
    accion = models.CharField(max_length=50, choices=ACCION_CHOICES)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.get_accion_display()} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')}"
