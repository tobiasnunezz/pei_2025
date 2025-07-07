from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Importa las vistas

urlpatterns = [
    path('', views.lista_tablero, name='lista_tablero'),  # Vista principal del tablero
    path('editar/<int:id>/', views.editar_avance, name='editar_avance'),
    path('admin/perfiles/', views.gestionar_perfiles, name='gestionar_perfiles'),
    path('panel/', views.admin_tablero, name='admin_tablero'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('historial/<int:id>/', views.ver_historial, name='ver_historial'),
    path('bitacora/', views.ver_bitacora_accesos, name='bitacora_accesos'),


    # Rutas para cambiar contraseña
    path('cambiar-contraseña/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/cambiar-contraseña-hecho/'
    ), name='cambiar_contrasena'),

    path('cambiar-contraseña-hecho/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='cambiar_contrasena_hecho'),
]
