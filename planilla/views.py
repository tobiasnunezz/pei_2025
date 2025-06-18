from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Tablero, HistorialCambio, PerfilUsuario, HistorialAvance
from .forms import AvanceForm, TableroCompletoForm, PerfilUsuarioForm, CrearUsuarioForm
from collections import defaultdict
import csv

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

    if usuario.is_staff:
        form = TableroCompletoForm(request.POST or None, instance=tablero)
    else:
        if tablero.responsable != usuario.perfilusuario.responsable:
            return redirect('lista_tablero')
        form = AvanceForm(request.POST or None, instance=tablero)

    if request.method == 'POST' and form.is_valid():
        # Captura de valores antiguos
        antiguo_avance = tablero.avance
        antigua_observacion = getattr(tablero, 'observacion', '')
        antiguo_nivel = tablero.nivel
        antigua_accion = tablero.accion

        form.save()  # Guarda nuevos valores
        nuevo_avance = form.cleaned_data.get('avance', '')
        nueva_observacion = form.cleaned_data.get('observacion', '')
        nuevo_nivel = tablero.nivel
        nueva_accion = tablero.accion

        # HistorialCambio por campo
        campos = [
            ('avance', antiguo_avance, nuevo_avance),
            ('observacion', antigua_observacion, nueva_observacion),
            ('nivel', antiguo_nivel, nuevo_nivel),
            ('accion', antigua_accion, nueva_accion),
        ]
        for campo, anterior, nuevo in campos:
            if (anterior or '') != (nuevo or ''):
                HistorialCambio.objects.create(
                    usuario=usuario,
                    indicador=tablero,
                    campo=campo,
                    valor_anterior=anterior or '',
                    valor_nuevo=nuevo or ''
                )

        # HistorialAvance general
        if (antiguo_avance != nuevo_avance) or (antigua_observacion != nueva_observacion):
            HistorialAvance.objects.create(
                tablero=tablero,
                usuario=usuario,
                avance_anterior=antiguo_avance or '',
                avance_nuevo=nuevo_avance or '',
                observacion=nueva_observacion or ''
            )

        messages.success(request, 'Avance actualizado correctamente.')
        return redirect('lista_tablero')

    return render(request, 'planilla/editar_avance.html', {
        'form': form,
        'tablero': tablero
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

    return render(request, 'planilla/gestionar_perfiles.html', {
        'perfiles': perfiles,
        'form': form
    })

@login_required
def admin_tablero(request):
    tableros = Tablero.objects.all().order_by('orden')
    return render(request, 'planilla/admin_tablero.html', {'tableros': tableros})

@login_required
def exportar_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tablero.csv"'
    writer = csv.writer(response)
    writer.writerow(['Eje', 'Objetivo', 'Indicador', 'Meta', 'Avance', 'Nivel', 'Acción'])

    for t in Tablero.objects.all().order_by('orden'):
        writer.writerow([t.eje_estrategico, t.objetivo_estrategico, t.indicador,
                         t.meta_2025, t.avance, t.nivel, t.accion])
    return response

@login_required
def exportar_pdf(request):
    return HttpResponse("Exportar a PDF aún no implementado")

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
