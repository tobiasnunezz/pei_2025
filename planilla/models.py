from django.db import models
from django.contrib.auth.models import User

class Tablero(models.Model):
    eje_estrategico = models.CharField(max_length=255)
    objetivo_estrategico = models.TextField()
    indicador = models.TextField()
    meta_2025 = models.CharField(max_length=100)
    avance = models.FloatField(null=True, blank=True)
    nivel = models.CharField(max_length=50, blank=True)
    accion = models.CharField(max_length=50, blank=True)
    responsable = models.CharField(max_length=100, blank=True)

    def calcular_nivel_y_accion(self):
        if self.avance is None or self.meta_2025 in ["", None]:
            self.nivel = ""
            self.accion = ""
        else:
            try:
                meta = float(self.meta_2025.replace("%", ""))
                porcentaje = (self.avance / meta) * 100
                if porcentaje < 50:
                    self.nivel = "Bajo"
                    self.accion = "Correctiva"
                elif porcentaje < 90:
                    self.nivel = "Medio"
                    self.accion = "Preventiva"
                else:
                    self.nivel = "Alto"
                    self.accion = "Continuar"
            except ValueError:
                self.nivel = ""
                self.accion = ""
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    responsable = models.CharField(max_length=100)  # Ej: GT, GPD, GSC, etc.

    def __str__(self):
        return f"{self.user.username} - {self.responsable}"