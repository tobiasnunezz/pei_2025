from django.contrib import admin
#from .models import ReglaAcceso
from .models import Tablero




@admin.register(Tablero)
class TableroAdmin(admin.ModelAdmin):
    list_display = ('eje_estrategico', 'indicador', 'avance', 'nivel', 'accion', 'responsable')
    list_filter = ('nivel', 'avance')
    search_fields = ('indicador', 'objetivo_estrategico')
