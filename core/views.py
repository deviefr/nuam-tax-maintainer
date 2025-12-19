import csv
import io
import re
import pandas as pd
from decimal import Decimal
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import TaxQualification, AuditLog
from .forms import UploadFileForm, ManualEntryForm
from .services import calcular_factor_tributario
from django.http import HttpResponse
import unicodedata
from django.core.exceptions import ValidationError
from .validators import validar_rut 

def is_analyst(user):
    return user.is_superuser or user.is_staff or user.groups.filter(name='Analistas').exists()

def is_admin(user):
    return user.is_superuser 

def normalizar_columnas_inteligentes(df):
    mapa_renombre = {}
    for col in df.columns:
        col_str = str(col).lower().strip()
        col_str = ''.join(
            c for c in unicodedata.normalize('NFD', col_str)
            if unicodedata.category(c) != 'Mn'
        )
        if 'rut' in col_str:
            mapa_renombre[col] = 'RUT'
        elif 'razon' in col_str or 'social' in col_str:
            mapa_renombre[col] = 'RazonSocial'
        elif 'monto' in col_str:
            mapa_renombre[col] = 'Monto'
        elif 'fecha' in col_str or 'vigencia' in col_str:
            mapa_renombre[col] = 'Fecha'
    df.rename(columns=mapa_renombre, inplace=True)
    return df

def registrar_auditoria(user, action, rut, old_value="-", new_value="-"):
    AuditLog.objects.create(
        user=user,
        action=action,
        target_rut=rut,
        previous_value=str(old_value),
        new_value=str(new_value)
    )

@login_required
def home(request):
    query = request.GET.get('q')
    results = TaxQualification.objects.all()
    if query:
        results = TaxQualification.objects.filter(rut_emisor__icontains=query)
    if request.GET.get('export') == 'csv':
        return export_csv(results) 
    return render(request, 'core/home.html', {'results': results, 'query': query})

@login_required
def export_csv(queryset):
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

@login_required
@user_passes_test(is_analyst, login_url='home')
def create_tax(request):
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
@user_passes_test(is_analyst, login_url='home')
def edit_tax(request, id):
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
@user_passes_test(is_analyst, login_url='home')
def delete_tax(request, id):
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
@user_passes_test(is_admin, login_url='home')
def audit_view(request):
    logs = AuditLog.objects.all()
    return render(request, 'core/audit_log.html', {'logs': logs})

@login_required
@user_passes_test(is_analyst, login_url='home')
def upload_data(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                if file.name.endswith('.csv'):
                    file_data = file.read()
                    try:
                        decoded_file = file_data.decode('utf-8')
                    except UnicodeDecodeError:
                        decoded_file = file_data.decode('latin-1')
                    io_string = io.StringIO(decoded_file)
                    df = pd.read_csv(io_string, sep=None, engine='python')
                else:
                    df = pd.read_excel(file)

                df = normalizar_columnas_inteligentes(df)
                
                required_columns = ['RUT', 'RazonSocial', 'Monto', 'Fecha']
                missing_cols = [col for col in required_columns if col not in df.columns]
                
                if missing_cols:
                    columnas_encontradas = ", ".join(df.columns.tolist())
                    raise KeyError(f"Faltan: {', '.join(missing_cols)}. El sistema detectó estas columnas: [{columnas_encontradas}]")
                
                df.dropna(subset=['RUT', 'Monto'], inplace=True)
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
                
                success_count = 0
                errores_log = []
                
                for index, row in df.iterrows():
                    fila_excel = index + 2
                    try:
                        rut_formateado = validar_rut(row['RUT'])
                        
                        if pd.isna(row['Fecha']):
                            raise ValueError("Formato de fecha inválido (Use DD-MM-YYYY)")
                            
                        monto_raw = str(row['Monto']).replace('.', '').replace(',', '.')
                        try:
                            monto_dec = Decimal(monto_raw)
                            if monto_dec < 0: raise ValueError("El monto no puede ser negativo")
                        except:
                            raise ValueError("El monto no es un número válido")

                        factor_calc = calcular_factor_tributario(monto_dec)
                        
                        TaxQualification.objects.create(
                            rut_emisor=rut_formateado,
                            razon_social=row['RazonSocial'],
                            monto=monto_dec,
                            factor=factor_calc,
                            fecha_vigencia=row['Fecha'].date()
                        )
                        success_count += 1

                    except ValidationError as e:
                        errores_log.append(f"Fila {fila_excel} (RUT): {str(e.message)}")
                    except Exception as e:
                        errores_log.append(f"Fila {fila_excel}: {str(e)}")
                
                registrar_auditoria(
                    user=request.user,
                    action="CARGA_MASIVA",
                    rut="VARIOS",
                    old_value="-",
                    new_value=f"Procesados: {success_count} | Fallidos: {len(errores_log)}"
                )

                if success_count > 0:
                    messages.success(request, f'Se cargaron {success_count} registros correctamente.')
                
                if errores_log:
                    detalle = " | ".join(errores_log[:5])
                    if len(errores_log) > 5: detalle += f" ... y {len(errores_log)-5} más."
                    messages.warning(request, f'Se omitieron {len(errores_log)} filas por errores: {detalle}')

                return redirect('upload')

            except KeyError as e:
                messages.error(request, f'Error de estructura: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error crítico procesando archivo: {str(e)}')
                
    else:
        form = UploadFileForm()
            
    return render(request, 'core/upload.html', {'form': form})