from django.contrib import admin

# Register your models here.
from .models import TaxQualification, AuditLog

@admin.register(TaxQualification)
class TaxQualificationAdmin(admin.ModelAdmin):
    list_display = ('rut_emisor', 'razon_social', 'monto', 'factor', 'fecha_vigencia', 'created_at')
    search_fields = ('rut_emisor', 'razon_social')
    list_filter = ('fecha_vigencia',)
    ordering = ('-fecha_vigencia', 'rut_emisor')
    
    fieldsets = (
        ('Información del Emisor', {
            'fields': ('rut_emisor', 'razon_social')
        }),
        ('Datos Tributarios', {
            'fields': ('monto', 'factor', 'fecha_vigencia')
        }),
    )
    
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'target_rut')
    search_fields = ('user__username', 'target_rut', 'action')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'action', 'target_rut', 'previous_value', 'new_value', 'timestamp')
    
    def resumen_cambio(self, obj):
        return f"{obj.action} sobre {obj.target_rut} por {obj.user}"
    
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False