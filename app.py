"""
La Greta Te Escucha - version simple
Stack: Python (Flask) + HTML + CSS + JS + SQLite
"""

from flask import Flask, render_template, request, redirect, url_for, abort, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave-secreta-para-la-clase"
DB_NAME = "la_greta.db"
CLAVE_ADMIN = "admin123"

# Categorias del formulario. Cada una define su propio texto e intro.
CATEGORIAS = {
    "cuenta-pago": {
        "titulo": "Mi cuenta o pago",
        "descripcion": "Cobro incorrecto, ticket, pago",
        "intro": "Cuentanos que paso con tu cuenta, ticket o pago.",
        "descripcion_label": "Describe que paso",
        "whatsapp_obligatorio": True,
    },
    "atencion-servicio": {
        "titulo": "Atencion y servicio",
        "descripcion": "Mesero, recepcion, personal",
        "intro": "Cuentanos que paso con la atencion que recibiste.",
        "descripcion_label": "Cuentanos que paso",
    },
    "alimentos-bebidas": {
        "titulo": "Alimentos y bebidas",
        "descripcion": "Calidad, tiempo de espera, pedido",
        "intro": "Cuentanos que paso con tu pedido.",
        "descripcion_label": "Describe que paso",
    },
    "instalaciones": {
        "titulo": "Instalaciones",
        "descripcion": "Limpieza, banos, mobiliario",
        "intro": "Cuentanos que encontraste.",
        "descripcion_label": "Describe la situacion",
    },
    "seguridad": {
        "titulo": "Seguridad o situacion incomoda",
        "descripcion": "Cuentanos que paso",
        "intro": "Este espacio es para comunicarnos algo importante o incomodo.",
        "descripcion_label": "Cuentanos que paso",
    },
    "sugerencia": {
        "titulo": "Sugerencia",
        "descripcion": "Ideas para mejorar La Greta",
        "intro": "Nos encantaria escuchar tus ideas para mejorar La Greta.",
        "descripcion_label": "Cuentanos tu idea",
    },
}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            whatsapp TEXT,
            creado_en TEXT NOT NULL,
            resuelto INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Si la tabla ya existia de una version anterior sin esta columna, se agrega.
    columnas = []
    for columna in conn.execute("PRAGMA table_info(reportes)"):
        columnas.append(columna["name"])
    if "resuelto" not in columnas:
        conn.execute("ALTER TABLE reportes ADD COLUMN resuelto INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def formato_fecha(fecha_iso):
    fecha = datetime.fromisoformat(fecha_iso)
    return f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}"


def solo_digitos(texto):
    resultado = ""
    for caracter in texto:
        if caracter.isdigit():
            resultado += caracter
    return resultado


def siguiente_folio(conn):
    cursor = conn.execute("SELECT COUNT(*) AS total FROM reportes")
    total = cursor.fetchone()["total"]
    numero = total + 1
    return f"LG-{numero:05d}"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        clave = request.form.get("clave", "")
        if clave == CLAVE_ADMIN:
            session["logueado"] = True
            return redirect(url_for("reportes"))
        return redirect(url_for("login", error="1"))

    error = "Clave incorrecta." if request.args.get("error") else None
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logueado", None)
    return redirect(url_for("login"))


@app.route("/reportes")
def reportes():
    if not session.get("logueado"):
        return redirect(url_for("login"))

    categoria = request.args.get("categoria", "")
    folio = request.args.get("folio", "").strip()
    fecha = request.args.get("fecha", "")
    estado = request.args.get("estado", "pendiente")

    condiciones = []
    valores = []

    if categoria:
        condiciones.append("categoria = ?")
        valores.append(categoria)
    if folio:
        condiciones.append("folio LIKE ?")
        valores.append(f"%{folio}%")
    if fecha:
        condiciones.append("date(creado_en) = ?")
        valores.append(fecha)
    if estado == "pendiente":
        condiciones.append("resuelto = 0")
    elif estado == "resuelto":
        condiciones.append("resuelto = 1")

    orden = request.args.get("orden", "")
    direccion = request.args.get("direccion", "desc")
    if direccion not in ("asc", "desc"):
        direccion = "desc"

    consulta = "SELECT * FROM reportes"
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)

    if orden == "folio":
        consulta += f" ORDER BY folio {direccion}"
    elif orden == "fecha":
        consulta += f" ORDER BY creado_en {direccion}"
    else:
        consulta += " ORDER BY id DESC"

    conn = get_db()
    total_pendientes = conn.execute(
        "SELECT COUNT(*) FROM reportes WHERE resuelto = 0"
    ).fetchone()[0]

    # Se traen todos los reportes que cumplen el filtro y la paginacion
    # se hace en Python, cortando la lista con el pedazo que toca.
    todos_los_reportes = conn.execute(consulta, valores).fetchall()
    conn.close()

    total = len(todos_los_reportes)

    POR_PAGINA = 12
    total_paginas = total // POR_PAGINA
    if total % POR_PAGINA != 0:
        total_paginas += 1
    if total_paginas == 0:
        total_paginas = 1

    pagina = request.args.get("pagina", 1, type=int)
    if pagina < 1:
        pagina = 1
    if pagina > total_paginas:
        pagina = total_paginas

    inicio = (pagina - 1) * POR_PAGINA
    fin = inicio + POR_PAGINA
    filas = todos_los_reportes[inicio:fin]

    # Se arma una lista de reportes ya lista para mostrar en la tabla,
    # con la fecha bonita y el link de WhatsApp ya calculados.
    reportes_para_mostrar = []
    for fila in filas:
        if fila["whatsapp"]:
            whatsapp_link = "https://wa.me/52" + solo_digitos(fila["whatsapp"])
        else:
            whatsapp_link = None

        reportes_para_mostrar.append({
            "id": fila["id"],
            "folio": fila["folio"],
            "categoria": fila["categoria"],
            "descripcion": fila["descripcion"],
            "whatsapp": fila["whatsapp"],
            "whatsapp_link": whatsapp_link,
            "fecha_bonita": formato_fecha(fila["creado_en"]),
            "resuelto": fila["resuelto"],
        })

    filtros = {
        "categoria": categoria,
        "folio": folio,
        "fecha": fecha,
        "estado": estado,
        "orden": orden,
        "direccion": direccion,
    }
    return render_template(
        "reportes.html",
        reportes=reportes_para_mostrar,
        categorias=CATEGORIAS,
        filtros=filtros,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        total_pendientes=total_pendientes,
    )


@app.route("/reportes/<int:reporte_id>/resolver", methods=["POST"])
def resolver(reporte_id):
    if not session.get("logueado"):
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "UPDATE reportes SET resuelto = 1 WHERE id = ?", (reporte_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("reportes"))


@app.route("/")
def index():
    return render_template("index.html", categorias=CATEGORIAS)


@app.route("/reportar/<categoria>", methods=["GET", "POST"])
def reportar(categoria):
    config = CATEGORIAS.get(categoria)
    if config is None:
        abort(404)

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()
        whatsapp = request.form.get("whatsapp", "").strip()

        if not descripcion:
            return render_template(
                "reportar.html",
                categoria=categoria,
                config=config,
                error="Por favor describe lo sucedido.",
            )

        if config.get("whatsapp_obligatorio") and not whatsapp:
            return render_template(
                "reportar.html",
                categoria=categoria,
                config=config,
                error="Necesitamos tu WhatsApp para dar seguimiento a tu caso.",
            )

        conn = get_db()
        folio = siguiente_folio(conn)
        conn.execute(
            "INSERT INTO reportes (folio, categoria, descripcion, whatsapp, creado_en) "
            "VALUES (?, ?, ?, ?, ?)",
            (folio, categoria, descripcion, whatsapp or None, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("gracias", folio=folio))

    return render_template("reportar.html", categoria=categoria, config=config, error=None)


@app.route("/gracias/<folio>")
def gracias(folio):
    return render_template("gracias.html", folio=folio)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
