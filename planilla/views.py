from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse
from collections import defaultdict
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import Tablero, PerfilUsuario, HistorialCambio
from .forms import AvanceForm, TableroCompletoForm, PerfilUsuarioForm, CrearUsuarioForm

ORDEN_EJES = [
    "Desarrollo y Fomento del Sector",
    "Gestión de los Recursos Financieros",
    "Eficiencia Regulatoria",
    "Desarrollo Institucional y del Talento Humano",
]

@login_required
def lista_tablero(request):
    usuario = request.user
    if not usuario.is_authenticated:
        tableros = list(Tablero.objects.all())
    elif usuario.is_staff or usuario.is_superuser:
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

    if request.user.is_staff or request.user.is_superuser:
        FormClass = TableroCompletoForm
    else:
        if request.user.perfilusuario.responsable != tablero.responsable:
            return redirect('lista_tablero')
        FormClass = AvanceForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=tablero)
        if form.is_valid():
            tablero = form.save(commit=False)
            tablero.calcular_nivel_y_accion()
            tablero.save()
            messages.success(request, "Indicador actualizado correctamente.")
            return redirect('lista_tablero')
    else:
        form = FormClass(instance=tablero)

    return render(request, 'planilla/editar_avance.html', {
        'form': form,
        'tablero': tablero,
        'es_admin': request.user.is_staff
    })

@staff_member_required
def gestionar_perfiles(request):
    query = request.GET.get('q', '')
    perfiles = PerfilUsuario.objects.select_related('user').filter(
        user__username__icontains=query
    )

    if request.method == 'POST' and 'crear_usuario' in request.POST:
        crear_form = CrearUsuarioForm(request.POST)
        if crear_form.is_valid():
            crear_form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('gestionar_perfiles')
    else:
        crear_form = CrearUsuarioForm()

    if request.method == 'POST' and 'perfil_id' in request.POST:
        perfil_id = request.POST.get('perfil_id')
        perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
        form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, f"Responsable de {perfil.user.username} actualizado.")
            return redirect('gestionar_perfiles')

    forms_por_perfil = [
        (perfil, PerfilUsuarioForm(instance=perfil, prefix=str(perfil.id)))
        for perfil in perfiles
    ]

    return render(request, 'planilla/gestionar_perfiles.html', {
        'forms_por_perfil': forms_por_perfil,
        'crear_form': crear_form,
        'query': query
    })

@staff_member_required
def admin_tablero(request):
    tableros = list(Tablero.objects.all())
    agrupado = defaultdict(lambda: defaultdict(list))
    for t in tableros:
        eje = (t.eje_estrategico or "").strip()
        objetivo = (t.objetivo_estrategico or "").strip()
        agrupado[eje][objetivo].append(t)

    agrupado_ordenado = {}
    for eje in ORDEN_EJES:
        if eje in agrupado:
            agrupado_ordenado[eje] = dict(sorted(agrupado[eje].items()))

    return render(request, 'planilla/admin_tablero.html', {
        'agrupado': agrupado_ordenado
    })

@staff_member_required
def exportar_excel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tablero.csv"'

    writer = csv.writer(response)
    writer.writerow(['Eje Estratégico', 'Objetivo', 'Indicador', 'Meta 2025', 'Avance', 'Nivel', 'Acción', 'Responsable'])

    for t in Tablero.objects.all().order_by('orden'):
        writer.writerow([
            t.eje_estrategico,
            t.objetivo_estrategico,
            t.indicador,
            t.meta_2025,
            t.avance,
            t.nivel,
            t.accion,
            t.responsable
        ])

    return response

@staff_member_required
def exportar_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="tablero.pdf"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Tablero de Control - Exportación PDF")
    y -= 30
    p.setFont("Helvetica", 8)

    for t in Tablero.objects.all().order_by('orden'):
        linea = f"{t.eje_estrategico} | {t.objetivo_estrategico} | {t.indicador} | {t.meta_2025} | {t.avance} | {t.nivel} | {t.accion} | {t.responsable}"
        p.drawString(40, y, linea)
        y -= 15
        if y < 40:
            p.showPage()
            y = 750

    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@staff_member_required
def ver_historial(request, id):
    tablero = get_object_or_404(Tablero, id=id)
    historial = HistorialCambio.objects.filter(indicador=tablero).order_by('-fecha')

    return render(request, 'planilla/historial_cambios.html', {
        'tablero': tablero,
        'historial': historial
    })