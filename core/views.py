import csv
import pandas as pd
from decimal import Decimal
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import TaxQualification, AuditLog
from .forms import UploadFileForm, ManualEntryForm
from .services import calcular_factor_tributario
from django.http import HttpResponse

# Funciones de vista
def registrar_auditoria(user, action, rut, old_value="-", new_value="-"):
    """
    funcion centralizada para logs HU-05
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        target_rut=rut,
        previous_value=str(old_value),
        new_value=str(new_value)
    )

# Vistas públicas (corredores)
def home(request):
    """
    buscador principal HU-04
    """
    query = request.GET.get('q')
    results = TaxQualification.objects.all()
    if query:
        results = TaxQualification.objects.filter(rut_emisor__icontains=query)
    
    # exportacion de datos HU-06
    if request.GET.get('export') == 'csv':
        return export_csv(results) 
        
    return render(request, 'core/home.html', {'results': results, 'query': query})

def export_csv(queryset):
    """
    exportacion de datos manteniendo formato HU-06
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_nuam.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['RUT Emisor', 'Razón Social', 'Monto', 'Factor', 'Fecha'])
    
    for obj in queryset:
        writer.writerow([
            obj.rut_emisor,
            obj.razon_social,
            obj.monto,
            obj.factor,
            obj.fecha_vigencia
        ])
    return response

# Vistas privadas (analistas)
def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def create_tax(request):
    """
    crear registros manuales HU-03
    """ 
    if request.method == 'POST':
        form = ManualEntryForm(request.POST)
        if form.is_valid():
            tax = form.save(commit=False)
            tax.factor = calcular_factor_tributario(tax.monto)
            tax.save()
            
            registrar_auditoria(request.user, "CREAR", tax.rut_emisor, "-", f"Monto: {tax.monto}")
            messages.success(request, 'Registro creado exitosamente.')
            return redirect('home')
    else:
        form = ManualEntryForm()
        return render(request, 'core/form_tax.html', {'form': form, 'title': 'Crear Calificación'}) 

@login_required
@user_passes_test(is_staff)
def edit_tax(request, id):
    """
    editar registros manuales HU-03
    """
    tax = get_object_or_404(TaxQualification, id=id)
    old_monto = tax.monto
    
    if request.method == 'POST':
        form = ManualEntryForm(request.POST, instance=tax)
        if form.is_valid():
            new_tax = form.save(commit=False)
            new_tax.factor = calcular_factor_tributario(new_tax.monto)
            new_tax.save()
            
            if old_monto != new_tax.monto:
                registrar_auditoria(request.user, "EDITAR", tax.rut_emisor, f"Monto: {old_monto}", f"Monto: {tax.monto}")
            messages.success(request, 'Registro actualizado exitosamente.')
            return redirect('home')
    else:
        form = ManualEntryForm(instance=tax)
    return render(request, 'core/form_tax.html', {'form': form, 'title': 'Editar Calificación'})
        
@login_required
@user_passes_test(is_staff)
def delete_tax(request, id):
    """
    eliminar registros manuales HU-03
    """
    tax = get_object_or_404(TaxQualification, id=id)
    
    if request.method == 'POST':
        rut_backup = tax.rut_emisor
        monto_backup = tax.monto
        tax.delete()
        
        registrar_auditoria(request.user, "ELIMINAR", tax.rut_emisor, f"Monto: {tax.monto}", "-")
        messages.success(request, 'Registro eliminado exitosamente.')
        return redirect('home')
    return render(request, 'core/confirm_delete.html', {'object': tax})

@login_required
@user_passes_test(is_staff)
def audit_view(request):
    """
    vista de auditoría HU-05
    """
    logs = AuditLog.objects.all()
    return render(request, 'core/audit_log.html', {'logs': logs})

@login_required
@user_passes_test(lambda u: u.is_staff)
def upload_data(request):
    """
    Carga Masiva de Datos (HU-01) con Auditoría (HU-05)
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                success_count = 0
                
                for _, row in df.iterrows():
                    monto_dec = Decimal(str(row['Monto'])) 
                    factor_calc = calcular_factor_tributario(monto_dec)
                    
                    TaxQualification.objects.create(
                        rut_emisor=row['RUT'],
                        razon_social=row['RazonSocial'],
                        monto=monto_dec,
                        factor=factor_calc,
                        fecha_vigencia=row['Fecha']
                    )
                    success_count += 1
                
                registrar_auditoria(
                    user=request.user,
                    action="CARGA_MASIVA",
                    rut="VARIOS",
                    old_val="-",
                    new_val=f"Se procesaron {success_count} registros desde {file.name}"
                )

                messages.success(request, f'¡Éxito! Se cargaron {success_count} registros correctamente.')
                return redirect('upload')

            except KeyError as e:
                messages.error(request, f'Error de formato: Falta la columna {str(e)} en el archivo.')
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                
    else:
        form = UploadFileForm()
            
    return render(request, 'core/upload.html', {'form': form})