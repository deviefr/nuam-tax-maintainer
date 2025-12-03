
from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('upload/', views.upload_data, name='upload'),
    
    #rutas CRUD y auditoría
    path('create/', views.create_tax, name='create_tax'),
    path('edit/<int:id>/', views.edit_tax, name='edit_tax'),
    path('delete/<int:id>/', views.delete_tax, name='delete_tax'),
    path('audit/', views.audit_view, name='audit_view'),
    
    # Rutas de autenticación
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), 
]
