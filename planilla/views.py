import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils.timezone import now
from django.template.loader import get_template
from django.utils.html import strip_tags
from collections import defaultdict
from django.core.files.base import ContentFile
from django.utils import timezone
import csv
import os
from django.conf import settings
from django.db.models import Prefetch
from weasyprint import HTML, CSS

from .models import Tablero, HistorialAvance, PerfilUsuario, BitacoraAcceso, Evidencia, EvidenciaHistorica
from .forms import AvanceForm, TableroCompletoForm, PerfilUsuarioForm, CrearUsuarioForm

logger = logging.getLogger(__name__)

ORDEN_EJES = [
    "Desarrollo y Fomento del Sector",
    "Gestión de los Recursos Financieros",
    "Eficiencia Regulatoria",
    "Desarrollo Institucional y del Talento Humano",
]

@login_required
def lista_tablero(request):
    usuario = request.user
    latest_historial_prefetch = Prefetch(
        'historialavance_set',
        queryset=HistorialAvance.objects.order_by('-fecha'),
        to_attr='latest_historial_list'
    )
    if usuario.is_staff or usuario.is_superuser:
        tableros = Tablero.objects.prefetch_related(latest_historial_prefetch).all()
    else:
        responsable = usuario.perfilusuario.responsable
        tableros = Tablero.objects.filter(responsable=responsable).prefetch_related(latest_historial_prefetch)

    # Adjuntamos la lista de evidencias a cada tablero para usarla en la plantilla
    for t in tableros:
        if t.latest_historial_list:
            t.latest_evidence = t.latest_historial_list[0].evidencias.all()
        else:
            t.latest_evidence = []

    agrupado = defaultdict(lambda: defaultdict(list))
    for t in tableros:
        eje = (t.eje_estrategico or "").strip()
        objetivo = (t.objetivo_estrategico or "").strip()
        agrupado[eje][objetivo].append(t)

    agrupado_ordenado = {}
    for eje in ORDEN_EJES:
        if eje in agrupado:
            agrupado_ordenado[eje] = dict(sorted(agrupado[eje].items()))

    return render(request, 'planilla/tablero.html', {
        'agrupado': agrupado_ordenado,
        'es_admin': usuario.is_staff or usuario.is_superuser
    })

@login_required
def editar_avance(request, id):
    tablero = get_object_or_404(Tablero, id=id)
    usuario = request.user

    if not usuario.is_authenticated:
        logger.warning("❌ Usuario no autenticado")
        return redirect('lista_tablero')

    if usuario.is_staff:
        form = AvanceForm(request.POST or None, request.FILES or None, instance=tablero)
    else:
        if tablero.responsable != usuario.perfilusuario.responsable:
            return redirect('lista_tablero')
        form = AvanceForm(request.POST or None, request.FILES or None, instance=tablero)

    if request.method == 'POST':
        form = AvanceForm(request.POST, request.FILES, instance=tablero)
        if form.is_valid():
            tablero_instance = form.save()

            nuevos_archivos = request.FILES.getlist('evidencias')
            ultimo_historial = HistorialAvance.objects.filter(tablero=tablero).order_by('-fecha').first()

            # --- LÓGICA MEJORADA ---

            # CASO 1: El usuario subió nuevos archivos.
            if nuevos_archivos:
                # Creamos un nuevo registro de historial que contendrá TODO (lo viejo y lo nuevo).
                nuevo_historial = HistorialAvance.objects.create(
                    tablero=tablero_instance,
                    usuario=request.user,
                    avance=form.cleaned_data.get('avance'),
                    observacion=form.cleaned_data.get('observacion')
                )

                # 1. Copiamos las referencias a los archivos antiguos al nuevo historial.
                if ultimo_historial:
                    for evidencia_antigua in ultimo_historial.evidencias.all():
                        Evidencia.objects.create(
                            historial_avance=nuevo_historial,
                            archivo=evidencia_antigua.archivo
                        )
                        # También creamos la copia histórica para mantener la consistencia.
                        EvidenciaHistorica.objects.create(
                            historial_avance=nuevo_historial,
                            archivo=evidencia_antigua.archivo,
                            nombre_original=evidencia_antigua.archivo.name.split('/')[-1]
                        )

                # 2. Añadimos los archivos nuevos.
                for f in nuevos_archivos:
                    Evidencia.objects.create(historial_avance=nuevo_historial, archivo=f)
                    f.seek(0) # Reiniciamos el puntero del archivo
                    EvidenciaHistorica.objects.create(
                        historial_avance=nuevo_historial,
                        nombre_original=f.name,
                        archivo=ContentFile(f.read(), name=f.name)
                    )
                
                messages.success(request, 'Avance guardado y nuevos archivos añadidos.')

            # CASO 2: El usuario NO subió archivos nuevos.
            else:
                # Si ya existe un historial, simplemente lo actualizamos.
                if ultimo_historial:
                    ultimo_historial.avance = form.cleaned_data.get('avance')
                    ultimo_historial.observacion = form.cleaned_data.get('observacion')
                    ultimo_historial.usuario = request.user
                    ultimo_historial.fecha = timezone.now() # Actualizamos la fecha de la última modificación
                    ultimo_historial.save()
                    messages.success(request, 'Avance actualizado correctamente.')
                # Si no había historial, lo creamos (primera vez que se guarda sin archivos).
                else:
                    HistorialAvance.objects.create(
                        tablero=tablero_instance,
                        usuario=request.user,
                        avance=form.cleaned_data.get('avance'),
                        observacion=form.cleaned_data.get('observacion')
                    )
                    messages.success(request, 'Avance guardado por primera vez.')

            return redirect('editar_avance', id=tablero.id)
    else:
        form = AvanceForm(instance=tablero)

    # La lógica para mostrar los archivos en la plantilla no cambia.
    context_historial = HistorialAvance.objects.filter(tablero=tablero).order_by('-fecha').first()
    return render(request, 'planilla/editar_avance.html', {
        'form': form,
        'tablero': tablero,
        'ultimo_historial': context_historial
    })

@login_required
def gestionar_perfiles(request):
    perfiles = PerfilUsuario.objects.all()
    form = CrearUsuarioForm()

    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('gestionar_perfiles')

    return render(request, 'planilla/gestionar_perfiles.html', {'perfiles': perfiles, 'form': form})

@login_required
def admin_tablero(request):
    tableros = Tablero.objects.all().order_by('orden')
    return render(request, 'planilla/admin_tablero.html', {'tableros': tableros})

@login_required
def exportar_excel(request):
    if not request.user.is_staff:
        return HttpResponse("No autorizado", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tablero.csv"'
    writer = csv.writer(response)
    writer.writerow(['Eje', 'Objetivo', 'Indicador', 'Meta', 'Avance', 'Nivel', 'Acción', 'Responsable', 'Observación'])

    for t in Tablero.objects.all().order_by('orden'):
        writer.writerow([
            t.eje_estrategico, t.objetivo_estrategico, strip_tags(t.indicador),
            t.meta_2025, t.avance, t.nivel, t.accion, t.responsable, t.observacion
        ])

    return response

@login_required
def exportar_pdf(request):
    if not request.user.is_staff:
        return HttpResponse("No autorizado", status=403)

    tableros = Tablero.objects.all().order_by('orden')
    agrupado = defaultdict(lambda: defaultdict(list))
    for t in tableros:
        eje = (t.eje_estrategico or "").strip()
        objetivo = (t.objetivo_estrategico or "").strip()
        agrupado[eje][objetivo].append(t)

    agrupado_ordenado = {}
    for eje in ORDEN_EJES:
        if eje in agrupado:
            agrupado_ordenado[eje] = dict(sorted(agrupado[eje].items()))

    template = get_template('planilla/tablero_pdf.html')
    html_string = template.render({
        'agrupado': agrupado_ordenado,
        'es_admin': True,
        'now': now(),               # ✅ FECHA Y HORA
        'user': request.user        # ✅ USUARIO ACTUAL
    })

    css_path = os.path.join(settings.BASE_DIR, 'static/css/pdf_tablero.css')
    css = CSS(filename=css_path)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[css])

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="tablero.pdf"'
    return response

@login_required
def ver_historial(request, id):
    tablero = get_object_or_404(Tablero, id=id)
    historial_avances = HistorialAvance.objects.filter(tablero=tablero).prefetch_related('evidencias').order_by('-fecha')
    return render(request, 'planilla/ver_historial.html', {
        'tablero': tablero,
        'historial_avances': historial_avances
    })

@login_required
def eliminar_evidencia(request, evidencia_id):
    """
    Vista para eliminar un archivo de evidencia específico.
    """
    # Buscamos el objeto Evidencia o devolvemos un error 404 si no existe
    evidencia = get_object_or_404(Evidencia, id=evidencia_id)
    
    # Guardamos el ID del tablero para poder redirigir al usuario
    # a la página de edición correcta después de eliminar el archivo.
    tablero_id = evidencia.historial_avance.tablero.id

    try:
        # Eliminamos el archivo físico del almacenamiento (media/evidencias/)
        evidencia.archivo.delete(save=True)
        # Eliminamos el registro de la base de datos
        evidencia.delete()
        messages.success(request, 'Archivo de evidencia eliminado correctamente.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el archivo: {e}')
        logger.error(f"Error al eliminar evidencia ID {evidencia_id}: {e}")

    # Redirigimos al usuario de vuelta a la página de edición del avance
    return redirect('editar_avance', id=tablero_id)

@login_required
@user_passes_test(lambda u: u.is_staff)
def ver_bitacora_accesos(request):
    accesos = BitacoraAcceso.objects.all().order_by('-fecha_hora')

    usuario = request.GET.get('usuario')
    accion = request.GET.get('accion')

    if usuario:
        accesos = accesos.filter(usuario__username__icontains=usuario)
    if accion:
        accesos = accesos.filter(accion=accion)

    return render(request, 'planilla/bitacora_accesos.html', {
        'accesos': accesos
    })