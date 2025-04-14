from django.db import models
from django.contrib.auth.models import User

class Tablero(models.Model):
    eje_estrategico = models.CharField(max_length=255)
    objetivo_estrategico = models.TextField()
    indicador = models.TextField()
    meta_2025 = models.CharField(max_length=100)
    avance = models.CharField(max_length=100, blank=True, null=True)  # Puede ser texto o número
    nivel = models.CharField(max_length=50, blank=True)
    accion = models.CharField(max_length=50, blank=True)
    responsable = models.CharField(max_length=100, blank=True)
    orden = models.PositiveIntegerField(default=0)

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
