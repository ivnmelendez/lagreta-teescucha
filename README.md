# La Greta Te Escucha

Sistema de reportes y sugerencias para clientes de La Greta. Hecho con Python
(Flask), HTML, CSS y la base de datos con SQLite.

## Que hace

- Formulario para reportar en 6 categorias (cuenta y pago, atención
  y servicio, alimentos y bebidas, instalaciones, seguridad, sugerencia).
- Panel de administrador con clave, filtros, orden y paginación.
- Cada reporte guarda un folio unico (LG-1001, LG-1002...).

## Como se corre

### Mac / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Despues abre `http://127.0.0.1:5000` en el navegador.

Panel de administrador: `http://127.0.0.1:5000/login` (clave en `app.py`,
variable `CLAVE_ADMIN`).

## La Estructura

```
app.py              rutas, logica, conexion a la base de datos
templates/          paginas HTML (Jinja)
static/style.css    estilos
la_greta.db          base de datos SQLite (se crea sola al arrancar)
```
