import re
from django.core.exceptions import ValidationError

def validar_rut(rut):
    rut_limpio = re.sub(r'[^0-9kK]', '', rut).upper()
    
    if not rut_limpio or len(rut_limpio) < 2:
        raise ValidationError("El RUT es inválido.")
    
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    
    try:
        suma = 0
        multiplo = 2
        for c in reversed(cuerpo):
            suma += int(c) * multiplo
            multiplo += 1
            if multiplo == 8:
                multiplo = 2
        
        resto = suma % 11
        dv_esperado = 11 - resto
        
        if dv_esperado == 11: dv_calculado = '0'
        elif dv_esperado == 10: dv_calculado = 'K'
        else: dv_calculado = str(dv_esperado)
        
        if dv != dv_calculado:
            raise ValidationError("El RUT es inválido.")
        
    except ValueError:
        raise ValidationError("El RUT es inválido.")
    
    cuerpo_formateado = "{:,}".format(int(cuerpo)).replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"
