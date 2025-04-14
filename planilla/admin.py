from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
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
        'orden',
    )
    list_editable = ('orden',)  # 👈 Editable desde la grilla
    ordering = ['orden']
    list_filter = ('eje_estrategico', 'nivel', 'responsable')
    search_fields = ('indicador', 'objetivo_estrategico', 'accion')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'responsable')
    search_fields = ('user__username', 'responsable')
