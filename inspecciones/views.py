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


# 🔹 SELECCIONAR
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
        self.setFont("Verdana", 8)
        self.drawCentredString(
            300,
            20,
            f"Página {self._pageNumber} de {total} / MPE-02-F-28-01 Versión: 12 / 2025-08-01"
        )


# 🔹 GENERAR INFORME
@login_required
def generar_informe(request):
    ids = request.POST.getlist('medidores')
    medidores = Medidor.objects.filter(id__in=ids) if ids else Medidor.objects.none()

    pdfmetrics.registerFont(TTFont('Verdana', r'C:\Windows\Fonts\verdana.ttf'))

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

    styles['Normal'].fontName = 'Verdana'
    styles['Normal'].fontSize = 9
    styles['Normal'].alignment = 4

    styles['Title'].fontName = 'Verdana'
    styles['Title'].fontSize = 10

    styles['Heading2'].fontName = 'Verdana'
    styles['Heading2'].fontSize = 10

    styles['Heading3'].fontName = 'Verdana'
    styles['Heading3'].fontSize = 9

    elementos = []

    elementos.append(Paragraph("INFORME TECNICO DE EVALUACION POST-DESTAPE DE MEDIDORES", styles['Title']))
    elementos.append(Spacer(1, 12))

    texto_obj = f"""
    El presente informe tiene como propósito documentar los hallazgos observados tras el proceso
    de destape y revisión visual interna de {medidores.count()} medidores de agua, los cuales fueron sometidos a
    evaluación técnica en el laboratorio de calibración.
    """
    elementos.append(Paragraph("<b>1. OBJETIVO</b>", styles['Heading2']))
    elementos.append(Paragraph(texto_obj, styles['Normal']))
    elementos.append(Spacer(1, 12))

    data = [['SERIAL', 'MODELO', 'AÑO', 'ESTADO', 'CODIGO']]
    for m in medidores:
        data.append([m.serial, m.modelo, m.anio, m.estado, m.codigo])

    tabla = Table(data)
    tabla.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8FA9C4")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ])

    elementos.append(Paragraph("<b>2. MEDIDORES INSPECCIONADOS</b>", styles['Heading2']))
    elementos.append(tabla)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("<b>3. OBSERVACIONES DETALLADAS</b>", styles['Heading2']))

    for i, m in enumerate(medidores, 1):
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(f"<b>3.{i} Medidor {m.serial}</b>", styles['Heading3']))

        if m.observaciones:
            elementos.append(Paragraph(m.observaciones, styles['Normal']))

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

        tabla_fotos.setStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])

        elementos.append(tabla_fotos)

    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("<b>4. CONCLUSIONES</b>", styles['Heading2']))
    elementos.append(Paragraph(
        "Los medidores presentan anomalías en sus componentes internos y requieren evaluación técnica.",
        styles['Normal']
    ))

    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("PAULA JULIA BLANCO H", styles['Normal']))
    elementos.append(Paragraph("Líder CN Laboratorio de calibración de medidores", styles['Normal']))
    elementos.append(Paragraph(f"Fecha: {datetime.now().date()}", styles['Normal']))

    def header_footer(canvas, doc):
        canvas.saveState()
        try:
            canvas.drawImage(r"E:\medidores\laboratorio_medidores\media\logo.png", 40, 750, width=520, height=70)
        except:
            pass
        try:
            canvas.drawImage(r"E:\medidores\laboratorio_medidores\media\pie.png", 40, 30, width=520, height=60)
        except:
            pass
        canvas.restoreState()

    doc.build(elementos, onFirstPage=header_footer, onLaterPages=header_footer, canvasmaker=NumberedCanvas)

    return response