import pandas as pd
from planilla.models import Tablero
from django.db import transaction

# Cargar el archivo Excel
df = pd.read_excel("pei.xlsx")

# Usar solo las columnas relevantes (las 3 primeras)
df = df.iloc[:, :3]
df.columns = ['eje', 'objetivo', 'indicador']

# Eliminar filas donde el indicador esté vacío o no sea texto
df = df[df['indicador'].notnull()]
df = df[df['indicador'].apply(lambda x: isinstance(x, str))]

@transaction.atomic
def actualizar_orden():
    errores = []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        indicador = row.indicador.strip()
        try:
            t = Tablero.objects.get(indicador__icontains=indicador)
            t.orden = i
            t.save()
            print(f"✔️ {i}: '{indicador}' actualizado (ID {t.id})")
        except Tablero.DoesNotExist:
            errores.append(indicador)
            print(f"❌ No encontrado: {indicador}")
        except Tablero.MultipleObjectsReturned:
            errores.append(indicador)
            print(f"⚠️ Múltiples coincidencias: {indicador}")

    if errores:
        print("\n🔴 Indicadores no actualizados:")
        for e in errores:
            print("-", e)

# Ejecutar la función
actualizar_orden()
