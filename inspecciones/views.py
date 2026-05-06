import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from .models import RegistroInspeccion, Medidor
from .forms import RegistroForm, MedidorFormSet

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# 🔹 Fuente
VERDANA_PATH = r'C:\Windows\Fonts\verdana.ttf'
if os.path.exists(VERDANA_PATH):
    pdfmetrics.registerFont(TTFont('Verdana', VERDANA_PATH))
    FONT = 'Verdana'
else:
    FONT = 'Helvetica'


# 🔹 LISTA
@login_required
def index(request):
    fecha_filtro = request.GET.get('fecha', '')
    if fecha_filtro:
        registros = RegistroInspeccion.objects.filter(fecha_informe=fecha_filtro).order_by('-fecha_informe')
    else:
        registros = RegistroInspeccion.objects.all().order_by('-fecha_informe')
    return render(request, 'index.html', {'registros': registros, 'fecha_filtro': fecha_filtro})


# 🔹 DETALLE
@login_required
def detalle_registro(request, pk):
    registro = get_object_or_404(RegistroInspeccion, pk=pk)
    return render(request, 'detalle.html', {'registro': registro})


# 🔹 CREAR
@login_required
def nuevo_registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        formset = MedidorFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            registro = form.save()
            medidores = formset.save(commit=False)
            for m in medidores:
                m.registro = registro
                m.save()
            return redirect('index')
    else:
        form = RegistroForm()
        formset = MedidorFormSet()
    return render(request, 'nuevo.html', {'form': form, 'formset': formset})


# 🔹 EDITAR
@login_required
def editar_registro(request, pk):
    registro = get_object_or_404(RegistroInspeccion, pk=pk)
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES, instance=registro)
        formset = MedidorFormSet(request.POST, request.FILES, instance=registro)
        if form.is_valid() and formset.is_valid():
            registro = form.save()
            medidores = formset.save(commit=False)
            for m in medidores:
                m.registro = registro
                m.save()
            for obj in formset.deleted_objects:
                obj.delete()
            return redirect('index')
    else:
        form = RegistroForm(instance=registro)
        formset = MedidorFormSet(instance=registro)
    return render(request, 'nuevo.html', {'form': form, 'formset': formset})


# 🔹 ELIMINAR
@login_required
def eliminar_registro(request, pk):
    registro = get_object_or_404(RegistroInspeccion, pk=pk)
    if request.method == 'POST':
        registro.delete()
    return redirect('index')


# 🔹 EXPORTAR EXCEL
@login_required
def exportar_excel(request):
    fecha_filtro = request.GET.get('fecha', '')
    if fecha_filtro:
        registros = RegistroInspeccion.objects.filter(fecha_informe=fecha_filtro)
    else:
        registros = RegistroInspeccion.objects.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Registros'

    encabezado = ['Fecha Informe', 'Fecha Despiece', 'Serial', 'Modelo', 'Año', 'Estado', 'Código', 'Alteración', 'Observaciones']
    for col, titulo in enumerate(encabezado, 1):
        cell = ws.cell(row=1, column=col, value=titulo)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='003366', end_color='003366', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')

    fila = 2
    for r in registros:
        for m in r.medidores.all():
            ws.cell(row=fila, column=1, value=str(r.fecha_informe))
            ws.cell(row=fila, column=2, value=str(r.fecha_despiece))
            ws.cell(row=fila, column=3, value=m.serial)
            ws.cell(row=fila, column=4, value=m.modelo)
            ws.cell(row=fila, column=5, value=m.anio)
            ws.cell(row=fila, column=6, value=m.estado)
            ws.cell(row=fila, column=7, value=m.codigo)
            ws.cell(row=fila, column=8, value=m.medidor_con_alteracion)
            ws.cell(row=fila, column=9, value=m.observaciones_encontradas)
            fila += 1

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="registros.xlsx"'
    wb.save(response)
    return response


# 🔹 SELECCIONAR MEDIDORES
@login_required
def seleccionar_medidores(request):
    fecha = request.GET.get('fecha')
    if fecha:
        medidores = Medidor.objects.filter(registro__fecha_informe=fecha)
    else:
        medidores = Medidor.objects.all()
    return render(request, 'seleccionar.html', {'medidores': medidores, 'fecha': fecha})


# 🔹 CANVAS PAGINACIÓN
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(total)
            super().showPage()
        super().save()

    def draw_footer(self, total):
        self.setFont(FONT, 8)
        self.drawCentredString(300, 20,
            f"Página {self._pageNumber} de {total} / MPE-02-F-28-01 Versión: 12 / 2025-08-01")


# 🔹 GENERAR INFORME PDF
@login_required
def generar_informe(request):
    ids = request.POST.getlist('medidores')
    medidores = Medidor.objects.filter(id__in=ids) if ids else Medidor.objects.none()
    fecha_informe = request.POST.get('fecha_informe', '')
    fecha_despiece = request.POST.get('fecha_despiece', '')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="informe.pdf"'

    doc = SimpleDocTemplate(response, rightMargin=40, leftMargin=40, topMargin=120, bottomMargin=100)
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = FONT
    styles['Normal'].fontSize = 9
    styles['Normal'].alignment = 4
    styles['Title'].fontName = FONT
    styles['Title'].fontSize = 10
    styles['Heading2'].fontName = FONT
    styles['Heading2'].fontSize = 10
    styles['Heading3'].fontName = FONT
    styles['Heading3'].fontSize = 9

    elementos = []
    elementos.append(Paragraph("INFORME TÉCNICO DE EVALUACIÓN DESPIECE DE MEDIDORES", styles['Title']))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"<b>Fecha del informe:</b> {fecha_informe}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Fecha del despiece:</b> {fecha_despiece}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>1. INFORMACIÓN DEL MEDIDOR</b>", styles['Heading2']))
    data = [['SERIAL', 'MODELO', 'AÑO', 'ESTADO', 'CODIGO', 'ALTERACIÓN']]
    for m in medidores:
        data.append([m.serial, m.modelo, m.anio, m.estado, m.codigo, m.medidor_con_alteracion])
    tabla = Table(data)
    tabla.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8FA9C4")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ])
    elementos.append(tabla)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>2. OBSERVACIÓN DEL DESPIECE</b>", styles['Heading2']))
    for i, m in enumerate(medidores, 1):
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph(f"<b>Medidor {m.serial}</b>", styles['Heading3']))
        if m.observaciones_encontradas:
            elementos.append(Paragraph(m.observaciones_encontradas, styles['Normal']))
        elementos.append(Spacer(1, 6))
        fotos = []
        for foto in [m.foto_1, m.foto_2, m.foto_3, m.foto_4]:
            if foto:
                try:
                    fotos.append(Image(foto.path, width=120, height=90))
                except:
                    fotos.append("")
            else:
                fotos.append("")
        tabla_fotos = Table([[fotos[0], fotos[1]], [fotos[2], fotos[3]]], colWidths=[250, 250])
        tabla_fotos.setStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        elementos.append(tabla_fotos)

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("PAULA JULIA BLANCO H", styles['Normal']))
    elementos.append(Paragraph("Líder CN Laboratorio de Calibración de Medidores", styles['Normal']))

    def header_footer(canvas, doc):
        canvas.saveState()
        try:
            logo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'logo.png')
            canvas.drawImage(logo, 40, 750, width=520, height=70)
        except:
            pass
        try:
            pie = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'pie.png')
            canvas.drawImage(pie, 40, 30, width=520, height=60)
        except:
            pass
        canvas.restoreState()

    doc.build(elementos, onFirstPage=header_footer, onLaterPages=header_footer, canvasmaker=NumberedCanvas)
    return response