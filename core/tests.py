from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from .models import TaxQualification
from .services import calcular_factor_tributario

class TaxSystemTests(TestCase):
    
    def setUp(self):
        # Crear usuario admin y usuario normal para pruebas
        self.admin_user = User.objects.create_superuser('admin', 'admin@nuam.com', 'password123')
        self.client = Client()

    def test_calculo_factor_exactitud(self):
        """Prueba Unitaria: Verifica que el motor de cálculo sea exacto (HU-02)"""
        monto = Decimal('1000000')
        esperado = Decimal('50.000000') # 1M * 0.00005
        resultado = calcular_factor_tributario(monto)
        self.assertEqual(resultado, esperado)

    def test_calculo_monto_negativo(self):
        """Prueba de Borde: Montos negativos deben dar error"""
        with self.assertRaises(ValueError):
            calcular_factor_tributario(Decimal('-100'))

    def test_acceso_protegido_upload(self):
        """Seguridad: Usuario no logueado no entra a carga"""
        response = self.client.get('/upload/')
        self.assertNotEqual(response.status_code, 200) # Debe redirigir (302)
        self.assertEqual(response.status_code, 302)

    def test_creacion_modelo(self):
        """Base de Datos: Integridad de datos"""
        tax = TaxQualification.objects.create(
            rut_emisor="11.222.333-k",
            razon_social="Test SpA",
            monto=1000,
            factor=0.05,
            fecha_vigencia="2025-12-31"
        )
        self.assertEqual(TaxQualification.objects.count(), 1)