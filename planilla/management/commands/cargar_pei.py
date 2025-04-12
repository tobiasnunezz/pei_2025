from django.core.management.base import BaseCommand
from planilla.models import Tablero
import pandas as pd

class Command(BaseCommand):
    help = 'Carga los indicadores del PEI desde el archivo pei.xlsx, sin duplicar existentes.'

    def handle(self, *args, **options):
        ruta_excel = 'pei.xlsx'  # Ruta relativa o absoluta al archivo

        try:
            xls = pd.ExcelFile(ruta_excel)
            df = xls.parse(xls.sheet_names[0])
            df.columns = [col.strip() for col in df.columns]  # Limpiar encabezados
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al leer el Excel: {e}"))
            return

        columnas = [
            'Ejes Estratégicos',
            'Objetivos Estratégicos',
            'Indicadores',
            'Meta 2025',
            'Avance',
            'Responsables'
        ]

        try:
            df = df[columnas].dropna(subset=['Indicadores'])
        except KeyError as e:
            self.stderr.write(self.style.ERROR(f"Columnas faltantes: {e}"))
            return

        nuevos = 0
        existentes = 0

        for _, fila in df.iterrows():
            if Tablero.objects.filter(indicador=fila['Indicadores']).exists():
                existentes += 1
                continue

            try:
                avance_valor = float(str(fila['Avance']).replace('%', '').strip())
            except:
                avance_valor = None

            tablero = Tablero(
                eje_estrategico=fila['Ejes Estratégicos'],
                objetivo_estrategico=fila['Objetivos Estratégicos'],
                indicador=fila['Indicadores'],
                meta_2025=str(fila['Meta 2025']),
                avance=avance_valor,
                responsable=str(fila['Responsables']).strip() if pd.notna(fila['Responsables']) else ''
            )
            tablero.calcular_nivel_y_accion()
            tablero.save()
            nuevos += 1

        self.stdout.write(self.style.SUCCESS(
            f"Carga finalizada: {nuevos} nuevos importados, {existentes} ya existían."
        ))
