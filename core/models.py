from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class TaxQualification(models.Model):
    """
    Entidad Core: almacena las calificaciones tributarias convertidas
    Se cumplen las HISTORIAS DE USUARIO 02 y 04
    """
    rut_emisor = models.CharField(max_length=12, db_index=True, verbose_name="RUT Emisor")
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social")
    monto = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    factor = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Factor Calculado")
    fecha_vigencia = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.rut_emisor} - {self.razon_social} ({self.fecha_vigencia})"
    
    class Meta:
        verbose_name = "Calificación Tributaria"
        verbose_name_plural = "Calificaciones Tributarias"
        ordering = ['-fecha_vigencia', 'rut_emisor']
        
class AuditLog(models.Model):
    """
    Seguridad: registro inmutable de acciones (RNF-02)
    registro inmutable HU-05
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    target_rut = models.CharField(max_length=12)
    previous_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
    
    class Meta:
        ordering = ['-timestamp']
    
    