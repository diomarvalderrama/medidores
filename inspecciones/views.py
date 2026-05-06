import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from .models import RegistroInspeccion, Medidor
from .forms import RegistroForm, MedidorFormSet

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.contrib.auth.decorators import login_required

from datetime import datetime


# 🔹 Fuente según sistema operativo
VERDANA_PATH = r'C:\Windows\Fonts\verdana.ttf'
if os.path.exists(VERDANA_PATH):
    pdfmetrics.registerFont(TTFont('Verdana', VERDANA_PATH))
    FONT = 'Verdana'
else:
    FONT = 'Helvetica'


# 🔹 LISTA
@login_required
def index(request):
    registros = RegistroInspeccion.objects.all().order_by('-fecha')
    return render(request, 'index.html', {'registros': registros})


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
            registro = form.save(commit=False)
            registro.save()

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

    return render(request, 'nuevo.html', {
        'form': form,
        'formset': formset
    })


# 🔹 ELIMINAR
@login_required
def eliminar_registro(request, pk):
    registro = get_object_or_404(RegistroInspeccion, pk=pk)
    if request.method == 'POST':
        registro.delete()
        return redirect('index')
    return redirect('index')


# 🔹 SELECCIONAR MEDIDORES
@login_required
def seleccionar_medidores(request):
    fecha = request.GET.get('fecha')

    if fecha:
        medidores = Medidor.objects.filter(registro__fecha=fecha)
    else:
        medidores = Medidor.objects.all()

    return render(request, 'seleccionar.html', {
        'medidores': medidores,
        'fecha': fecha
    })


# 🔹 CANVAS PARA PAGINACIÓN
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
        self.drawCentredString(
            300,
            20,
            f"Página {self._pageNumber} de {total} / MPE-02-F-28-01 Versión: 12 / 2025-08-01"
        )


# 🔹 GENERAR INFORME PDF
@login_required
def generar_informe(request):
    ids = request.POST.getlist('medidores')
    medidores = Medidor.objects.filter(id__in=ids) if ids else Medidor.objects.none()

    fecha_informe = request.POST.get('fecha_informe')
    fecha_despiece = request.POST.get('fecha_despiece')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="informe.pdf"'

    doc = SimpleDocTemplate(
        response,
        rightMargin=40,
        leftMargin=40,
        topMargin=120,
        bottomMargin=100
    )

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

    # 🔹 TÍTULO
    elementos.append(Paragraph("INFORME TÉCNICO DE EVALUACIÓN DESPIECE DE MEDIDORES", styles['Title']))
    elementos.append(Spacer(1, 10))

    # 🔹 FECHAS
    elementos.append(Paragraph(f"<b>Fecha del informe:</b> {fecha_informe}", styles['Normal']))
    elementos.append(Paragraph(f"<b>Fecha del despiece:</b> {fecha_despiece}", styles['Normal']))
    elementos.append(Spacer(1, 12))

    # 🔹 TABLA MEDIDORES
    data = [['SERIAL', 'MODELO', 'AÑO', 'ESTADO', 'CODIGO', 'ALTERACIÓN']]

    for m in medidores:
        data.append([
            m.serial,
            m.modelo,
            m.anio,
            m.estado,
            m.codigo,
            m.medidor_con_alteracion
        ])

    tabla = Table(data)
    tabla.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8FA9C4")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ])

    elementos.append(Paragraph("<b>1. INFORMACIÓN DEL MEDIDOR</b>", styles['Heading2']))
    elementos.append(tabla)
    elementos.append(Spacer(1, 12))

    # 🔹 OBSERVACIONES
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

        tabla_fotos = Table([
            [fotos[0], fotos[1]],
            [fotos[2], fotos[3]],
        ], colWidths=[250, 250])

        elementos.append(tabla_fotos)

    elementos.append(Spacer(1, 20))

    # 🔹 FIRMA
    try:
        firma = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'firma.png')
        elementos.append(Image(firma, width=150, height=50))
    except:
        pass

    elementos.append(Paragraph("PAULA JULIA BLANCO H", styles['Normal']))
    elementos.append(Paragraph("Líder CN Laboratorio de Calibración de Medidores", styles['Normal']))

    # 🔹 HEADER Y FOOTER
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

    doc.build(
        elementos,
        onFirstPage=header_footer,
        onLaterPages=header_footer,
        canvasmaker=NumberedCanvas
    )

    return response