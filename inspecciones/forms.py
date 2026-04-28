from django import forms
from .models import RegistroInspeccion, Medidor
from django.forms import inlineformset_factory


class RegistroForm(forms.ModelForm):
    fecha = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    class Meta:
        model = RegistroInspeccion
        fields = '__all__'


class MedidorForm(forms.ModelForm):
    class Meta:
        model = Medidor
        exclude = ('registro',)


MedidorFormSet = inlineformset_factory(
    RegistroInspeccion,
    Medidor,
    fields='__all__',
    extra=1,
    max_num=1,
    validate_max=True
)