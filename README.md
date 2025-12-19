# nuam-tax-maintainer

Sistema de Gestión de Calificaciones Tributarias desarrollado para el Holding NUAM (Bolsas de Santiago, Lima y Colombia). Este sistema centraliza, automatiza y audita la carga de factores tributarios.

## Características Principales
* **Carga Masiva Inteligente:** Procesa archivos Excel/CSV, detecta separadores automáticamente y valida RUTs chilenos fila por fila.
* **Roles Diferenciados (RBAC):**
  * **Administrador:** Gestión total (CRUD), Carga Masiva, Auditoría, Control de roles y accesos.
  * **Analista:** Gestión total (CRUD), Carga Masiva.
  * **Corredor:** Solo visualización, búsqueda y exportación de reportes.
* **Auditoría:** Registro inmutable de cada acción (quién, qué, valor anterior vs. nuevo).
* **Motor de Cálculo:** Conversión automática de montos a factores con precisión decimal.

## Tecnologías
* **Backend:** Django, Python
* **Procesamiento de Datos:** Pandas, Numpy
* **Frontend:** Bootstrap 5
* **Base de Datos:** SQLite

## Instalación y Ejecución

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/deviefr/nuam-tax-maintainer.git
   cd nuam-tax-maintainer

2. **Crear entorno virtual e instalar dependencias**
    ```bash
    python -m venv venv
    venv\Scripts\activate

    pip install -r requirements.txt
    (pandas, openpyxl, django)

3. **Migrar la base de datos**
    ```bash
    python manage.py makemigrations
    python manage.py migrate

4. **Crear Superusuario (Admin)**
    ```bash
    python manage.py createsuperuser

5. **Iniciar el servidor**
    ```bash
    python manage.py runserver

## Usuarios RBAC

| Rol      | Usuario   | Contraseña | Permisos |
|----------|-----------|------------|----------|
| Admin    | `admin`   | *(clave)* | Acceso total + Panel Django |
| Analista | `analista`| *(clave)* | Carga, Edición y Borrado *(Staff: Sí)* |
| Corredor | `corredor`| *(clave)* | Solo lectura y exportar *(Staff: No)* |

