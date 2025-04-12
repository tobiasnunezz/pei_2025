from django.core.management.base import BaseCommand
from planilla.models import Tablero

class Command(BaseCommand):
    help = "Corrige filas del tablero rellenando Ejes y Objetivos faltantes heredando el valor anterior."

    def handle(self, *args, **kwargs):
        todos = list(Tablero.objects.all().order_by("id"))
        ultimo_eje = None
        ultimo_objetivo = None
        corregidos = 0

        for t in todos:
            cambiado = False
            if t.eje_estrategico in [None, "", "nan", "NaN"]:
                t.eje_estrategico = ultimo_eje
                cambiado = True
            else:
                ultimo_eje = t.eje_estrategico

            if t.objetivo_estrategico in [None, "", "nan", "NaN"]:
                t.objetivo_estrategico = ultimo_objetivo
                cambiado = True
            else:
                ultimo_objetivo = t.objetivo_estrategico

            if cambiado:
                t.save()
                corregidos += 1

        self.stdout.write(self.style.SUCCESS(f"Se corrigieron {corregidos} registros con campos heredados."))
