from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from .models import Tablero, PerfilUsuario
from .models import HistorialCambio

@admin.register(Tablero)
class TableroAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'eje_estrategico',
        'objetivo_estrategico',
        'indicador',
        'meta_2025',
        'avance',
        'nivel',
        'accion',
        'responsable',
        # No muestres 'orden' aquí para evitar conflictos con drag-and-drop
    )
    ordering = ['eje_estrategico', 'orden']  # Orden inicial por eje y orden interno
    list_filter = ('eje_estrategico', 'nivel', 'responsable')
    search_fields = ('indicador', 'objetivo_estrategico', 'accion')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'responsable')
    search_fields = ('user__username', 'responsable')

@admin.register(HistorialCambio)
class HistorialCambioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'indicador', 'campo', 'valor_anterior', 'valor_nuevo')
    list_filter = ('usuario', 'campo', 'fecha')
    search_fields = ('indicador__indicador', 'campo', 'valor_anterior', 'valor_nuevo')