from decimal import Decimal

def calcular_factor_tributario(monto: Decimal) -> Decimal:
    """
    HU-02: conversión automática
    regla: factor = monto * 0.00005 (ejemplo ficticio)
    Se rendondea a 6 según el requerimiento y se cumple con el criterio de aceptación.
    """
    TASA_CONVERSION = Decimal('0.00005')
    if monto < 0:
        raise ValueError("El monto no puede ser negativo.")
    
    factor = monto * TASA_CONVERSION
    return round(factor, 6)
    