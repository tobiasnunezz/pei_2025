import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils.timezone import now
from django.template.loader import get_template
from django.utils.html import strip_tags
from collections import defaultdict
import csv

from weasyprint import HTML, CSS

from .models import Tablero, HistorialCambio, PerfilUsuario, HistorialAvance
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
    if usuario.is_staff or usuario.is_superuser:
        tableros = list(Tablero.objects.all())
    else:
        responsable = usuario.perfilusuario.responsable
        tableros = list(Tablero.objects.filter(responsable=responsable))

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

    if request.method == 'POST' and form.is_valid():
        logger.debug("🟢 Entró en form.is_valid() para el usuario %s", usuario.username)

        antiguo_avance = tablero.avance
        antigua_obs = tablero.observacion
        antigua_evidencia = tablero.evidencia.name if tablero.evidencia else ""

        nuevo_avance = form.cleaned_data.get('avance')
        nueva_obs = form.cleaned_data.get('observacion')
        nueva_evidencia = form.cleaned_data.get('evidencia')

        logger.debug("📝 Datos limpios: avance=%s, observacion=%s, evidencia=%s", nuevo_avance, nueva_obs, nueva_evidencia)

        form.save()
        logger.debug("✅ form.save() ejecutado correctamente para tablero id=%s", tablero.id)

        logger.debug("📋 Comparando datos para detectar cambios...")
        logger.debug("Avance anterior: %s / nuevo: %s", antiguo_avance, nuevo_avance)
        logger.debug("Obs anterior: %s / nueva: %s", antigua_obs, nueva_obs)
        logger.debug("Evidencia anterior: %s / nueva: %s", antigua_evidencia, nueva_evidencia)

        hubo_cambio = False

        if antiguo_avance != nuevo_avance:
            logger.debug("📌 Cambio en avance detectado")
            HistorialCambio.objects.create(
                usuario=usuario,
                indicador=tablero,
                campo='avance',
                valor_anterior=antiguo_avance or '',
                valor_nuevo=nuevo_avance or ''
            )
            hubo_cambio = True

        if antigua_obs != nueva_obs:
            logger.debug("📌 Cambio en observación detectado")
            HistorialCambio.objects.create(
                usuario=usuario,
                indicador=tablero,
                campo='observacion',
                valor_anterior=antigua_obs or '',
                valor_nuevo=nueva_obs or ''
            )
            hubo_cambio = True

        if nueva_evidencia:
            nueva_evidencia_nombre = nueva_evidencia.name
            if antigua_evidencia != nueva_evidencia_nombre:
                logger.debug("📌 Cambio en evidencia detectado")
                HistorialCambio.objects.create(
                    usuario=usuario,
                    indicador=tablero,
                    campo='evidencia',
                    valor_anterior=antigua_evidencia or '',
                    valor_nuevo=nueva_evidencia_nombre or ''
                )
                hubo_cambio = True

        if hubo_cambio:
            try:
                HistorialAvance.objects.create(
                    tablero=tablero,
                    usuario=usuario,
                    avance_anterior=antiguo_avance or '',
                    avance_nuevo=nuevo_avance or '',
                    observacion=nueva_obs or ''
                )
                logger.info(f"✅ Cambio registrado por: {usuario.username}")
            except Exception as e:
                logger.error("❌ Error al guardar en HistorialAvance: %s", str(e))

        messages.success(request, 'Avance actualizado correctamente.')
        return redirect('lista_tablero')

    return render(request, 'planilla/editar_avance.html', {'form': form, 'tablero': tablero})

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
        'es_admin': True
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="tablero.pdf"'
    return response

@login_required
def ver_historial(request, id):
    tablero = get_object_or_404(Tablero, id=id)
    historial_cambios = HistorialCambio.objects.filter(indicador=tablero).order_by('-fecha')
    historial_avances = HistorialAvance.objects.filter(tablero=tablero).order_by('-fecha')
    return render(request, 'planilla/ver_historial.html', {
        'tablero': tablero,
        'historial': historial_cambios,
        'historial_avances': historial_avances
    })
