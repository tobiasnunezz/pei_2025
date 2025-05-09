# planilla/urls.py
from django.urls import path
from . import views  # Importa las vistas

urlpatterns = [
    path('', views.lista_tablero, name='lista_tablero'),  # Asegúrate de usar la vista correcta aquí
    path('editar/<int:id>/', views.editar_avance, name='editar_avance'),
    path('admin/perfiles/', views.gestionar_perfiles, name='gestionar_perfiles'),
    path('panel/', views.admin_tablero, name='admin_tablero'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('historial/<int:id>/', views.ver_historial, name='ver_historial'),
]
