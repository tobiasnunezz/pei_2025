from django.contrib import admin
from .models import Tablero, PerfilUsuario

@admin.register(Tablero)
class TableroAdmin(admin.ModelAdmin):
    list_display = (
        'eje_estrategico',
        'objetivo_estrategico',
        'indicador',
        'meta_2025',
        'avance',
        'nivel',
        'accion',
        'responsable',
    )
    list_editable = (
        'meta_2025',
        'avance',
        'nivel',
        'accion',
        'responsable',
    )
    list_filter = ('eje_estrategico', 'nivel', 'responsable')
    search_fields = ('indicador', 'objetivo_estrategico', 'accion')
    ordering = ('eje_estrategico', 'objetivo_estrategico')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'responsable')
    search_fields = ('user__username', 'responsable')
