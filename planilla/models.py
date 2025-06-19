from django.db import models
from django.contrib.auth.models import User

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
    evidencia = models.FileField(upload_to='evidencias/', blank=True, null=True)
    
    def calcular_nivel_y_accion(self):
        avance = (self.avance or "").strip().lower()
        try:
            valor = float(avance)
            if valor == 0:
                self.nivel = "No existe avance"
                self.accion = "Correctiva"
            elif valor < 25:
                self.nivel = "Bajo"
                self.accion = "Correctiva"
            elif valor < 50:
                self.nivel = "Aceptable"
                self.accion = "Preventiva"
            elif valor < 75:
                self.nivel = "Medio"
                self.accion = "Preventiva"
            elif valor < 90:
                self.nivel = "Satisfactorio"
                self.accion = "Analizar tendencias"
            else:
                self.nivel = "Óptimo"
                self.accion = "Analizar tendencias"
        except ValueError:
            if avance in ["no iniciado"]:
                self.nivel = "No existe avance"
                self.accion = "Correctiva"
            elif avance in ["en proceso"]:
                self.nivel = "Medio"
                self.accion = "Preventiva"
            elif avance in ["aprobado", "presentado", "aprobada", "presentada"]:
                self.nivel = "Óptimo"
                self.accion = "Analizar tendencias"
            else:
                self.nivel = ""
                self.accion = ""

    class Meta:
        ordering = ['orden']

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    responsable = models.CharField(max_length=100)

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
    tablero = models.ForeignKey(Tablero, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    avance_anterior = models.CharField(max_length=255)
    avance_nuevo = models.CharField(max_length=255)
    observacion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tablero.indicador} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
