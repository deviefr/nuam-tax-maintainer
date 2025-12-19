from django import forms
from .models import TaxQualification
from .validators import validar_rut

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Seleccione un archivo CSV/Excel')
    
class ManualEntryForm(forms.ModelForm):
    class Meta:
        model = TaxQualification
        fields = ['rut_emisor', 'razon_social', 'monto', 'fecha_vigencia']
        widgets = {
            'fecha_vigencia': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rut_emisor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9',
                }),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
    def clean_rut_emisor(self):
        rut = self.cleaned_data.get('rut_emisor', '')
        return validar_rut(rut)
    
