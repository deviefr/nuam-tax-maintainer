from django import forms
from .models import TaxQualification

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Seleccione un archivo CSV/Excel')
    
class ManualEntryForm(forms.ModelForm):
    class Meta:
        model = TaxQualification
        fields = ['rut_emisor', 'razon_social', 'monto', 'fecha_vigencia']
        widgets = {
            'fecha_vigencia': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rut_emisor': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
        }