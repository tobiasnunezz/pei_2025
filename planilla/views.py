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
from django.core.files.base import ContentFile
import csv
import os
import uuid
from pathlib import Path
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

    if request.method == 'POST':
        form = AvanceForm(request.POST, request.FILES, instance=tablero)
        if form.is_valid():
            tablero_instance = form.save()
            
            # Crea la nueva instantánea histórica INCONDICIONALMENTE
            nuevo_historial = HistorialAvance.objects.create(
                tablero=tablero_instance,
                usuario=request.user,
                avance=form.cleaned_data.get('avance'),
                observacion=form.cleaned_data.get('observacion')
            )

            # 1. Procesa los archivos que el usuario decidió CONSERVAR
            ids_conservados_str = request.POST.get('evidencias_conservadas', '')
            if ids_conservados_str:
                ids_conservados = [int(id) for id in ids_conservados_str.split(',') if id.isdigit()]
                evidencias_a_copiar = Evidencia.objects.filter(id__in=ids_conservados)
                
                for evidencia_antigua in evidencias_a_copiar:
                    try:
                        with evidencia_antigua.archivo.open('rb') as f:
                            contenido = f.read()
                        
                        nombre_base = evidencia_antigua.archivo.name.split('/')[-1]
                        
                        Evidencia.objects.create(
                            historial_avance=nuevo_historial,
                            archivo=ContentFile(contenido, name=nombre_base)
                        )
                    except (IOError, FileNotFoundError) as e:
                        logger.error(f"Error al copiar archivo: {e}")

            # 2. Procesa los archivos NUEVOS
            for f in request.FILES.getlist('evidencias'):
                Evidencia.objects.create(historial_avance=nuevo_historial, archivo=f)
                f.seek(0)
                EvidenciaHistorica.objects.create(
                    historial_avance=nuevo_historial,
                    nombre_original=f.name,
                    archivo=ContentFile(f.read(), name=f.name)
                )

            messages.success(request, 'Avance guardado. El historial ha sido actualizado.')
            return redirect('editar_avance', id=tablero.id)
    else:
        form = AvanceForm(instance=tablero)

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