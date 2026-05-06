from django import forms
from .models import RegistroInspeccion, Medidor
from django.forms import inlineformset_factory


class RegistroForm(forms.ModelForm):
    fecha_informe = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_despiece = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = RegistroInspeccion
        fields = '__all__'


class MedidorForm(forms.ModelForm):
    class Meta:
        model = Medidor
        exclude = ('registro',)
        labels = {
            'medidor_con_alteracion': 'Medidor con alteración',
            'observaciones_encontradas': 'Observaciones del despiece',
        }
        widgets = {
            'serial': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'medidor_con_alteracion': forms.Select(attrs={'class': 'form-control'}),
            'observaciones_encontradas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


MedidorFormSet = inlineformset_factory(
    RegistroInspeccion,
    Medidor,
    form=MedidorForm,
    extra=1,
    max_num=1,
    validate_max=True
)