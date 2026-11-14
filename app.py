from pathlib import Path
from datetime import datetime
import json
import os

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

from graficas import cargar_datos


BASE_DIR = Path(__file__).resolve().parent
GRAFICAS_DIR = BASE_DIR / "graficas"
app = Flask(__name__)


def cargar_configuracion_local() -> None:
    """Carga pares KEY=VALUE de .env sin imprimir valores sensibles."""
    archivo_env = BASE_DIR / ".env"
    if not archivo_env.exists():
        return
    for linea in archivo_env.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valor = valor.strip().strip("\"'")
        os.environ.setdefault(clave.strip(), valor)


cargar_configuracion_local()


CHAT_COLUMNAS = {
    "DEPARTAMENTO": "DEPARTAMENTO",
    "MUNICIPIO": "MUNICIPIO",
    "ESTADOS": "ESTADOS",
    "TIPO_CONECTIVIDAD": "TIPO_CONECTIVIDAD",
}
CHAT_METRICAS = {
    "USUARIOS_ACTIVOS_MES": "usuarios activos del mes",
    "VELOCIDAD_CONEXION_BAJADA": "velocidad de bajada (Mbps)",
    "VELOCIDAD_CONEXION_SUBIDA": "velocidad de subida (Mbps)",
    "INVERSION": "inversión reportada (COP)",
    "TRAFICO_MENSUAL_BAJADA": "tráfico mensual de bajada",
    "TRAFICO_MENSUAL_SUBIDA": "tráfico mensual de subida",
}


def formatear_fecha(fecha: datetime | pd.Timestamp) -> str:
    meses = (
        "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
        "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
    )
    return f"{fecha.day:02d} {meses[fecha.month - 1]} {fecha.year}"


def preparar_datos() -> pd.DataFrame:
    datos = cargar_datos().copy()
    datos["ESTADOS"] = datos["ESTADOS"].fillna("SIN INFORMACIÓN")
    datos["DEPARTAMENTO"] = datos["DEPARTAMENTO"].fillna("SIN INFORMACIÓN")
    datos["TIPO_CONECTIVIDAD"] = datos["TIPO_CONECTIVIDAD"].fillna("SIN INFORMACIÓN")
    return datos


def filtrar_datos(datos: pd.DataFrame) -> pd.DataFrame:
    departamento = request.args.get("departamento", "").strip()
    estado = request.args.get("estado", "").strip()
    conectividad = request.args.get("conectividad", "").strip()

    if departamento:
        datos = datos[datos["DEPARTAMENTO"].eq(departamento)]
    if estado:
        datos = datos[datos["ESTADOS"].eq(estado)]
    if conectividad:
        datos = datos[datos["TIPO_CONECTIVIDAD"].eq(conectividad)]
    return datos


@app.get("/")
def dashboard():
    datos = preparar_datos()
    filtrados = filtrar_datos(datos)
    departamentos = sorted(datos["DEPARTAMENTO"].unique())
    estados = sorted(datos["ESTADOS"].unique())
    conectividades = sorted(datos["TIPO_CONECTIVIDAD"].unique())

    usuarios = filtrados["USUARIOS_ACTIVOS_MES"].fillna(0).sum()
    velocidad = filtrados["VELOCIDAD_CONEXION_BAJADA"].dropna().mean()
    inversion = filtrados["INVERSION"].fillna(0).sum()
    fecha = datos["FECHA_CORTE"].dropna().max()
    fecha_proyeccion_usuarios = datetime.fromtimestamp(
        (GRAFICAS_DIR / "regresion_usuarios.png").stat().st_mtime
    )
    fecha_proyeccion_operacion = datetime.fromtimestamp(
        (GRAFICAS_DIR / "regresion_operacion.png").stat().st_mtime
    )

    resumen_estado = (
        filtrados["ESTADOS"].value_counts().rename_axis("label").reset_index(name="value")
    )
    resumen_departamento = (
        filtrados["DEPARTAMENTO"]
        .value_counts()
        .head(10)
        .rename_axis("label")
        .reset_index(name="value")
    )

    return render_template(
        "index.html",
        departamentos=departamentos,
        estados=estados,
        conectividades=conectividades,
        resumen_estado=resumen_estado.to_dict("records"),
        resumen_departamento=resumen_departamento.to_dict("records"),
        total_centros=len(filtrados),
        total_usuarios=int(usuarios),
        velocidad_promedio=round(velocidad, 1) if pd.notna(velocidad) else 0,
        inversion=inversion,
        fecha_corte=formatear_fecha(fecha) if pd.notna(fecha) else "SIN FECHA",
        fecha_actual=formatear_fecha(datetime.now()),
        fecha_proyeccion_usuarios=formatear_fecha(fecha_proyeccion_usuarios),
        fecha_proyeccion_operacion=formatear_fecha(fecha_proyeccion_operacion),
        filtros={
            "departamento": request.args.get("departamento", ""),
            "estado": request.args.get("estado", ""),
            "conectividad": request.args.get("conectividad", ""),
        },
    )


@app.get("/api/resumen")
def api_resumen():
    datos = filtrar_datos(preparar_datos())
    velocidad = datos["VELOCIDAD_CONEXION_BAJADA"].dropna().mean()
    return jsonify(
        {
            "centros": len(datos),
            "usuarios": int(datos["USUARIOS_ACTIVOS_MES"].fillna(0).sum()),
            "velocidad": round(velocidad, 1) if pd.notna(velocidad) else 0,
        }
    )


@app.post("/api/chat")
def api_chat():
    """Interpreta la pregunta con Gemini y ejecuta solo cálculos permitidos."""
    payload = request.get_json(silent=True) or {}
    pregunta = payload.get("pregunta", "")
    if not isinstance(pregunta, str) or not pregunta.strip():
        return jsonify({"success": False, "respuesta": "Escribe una pregunta para empezar."}), 400
    pregunta = pregunta.strip()[:1000]

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            "success": False,
            "respuesta": "El chatbot aún no está configurado. Añade GEMINI_API_KEY al archivo .env y reinicia la aplicación.",
        }), 503

    try:
        from google import genai
        from google.genai import types

        modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        cliente = genai.Client(api_key=api_key)
        instruccion = f"""Eres un intérprete de preguntas sobre centros digitales rurales en Colombia.
Convierte la pregunta del usuario en un plan JSON. No respondas la pregunta ni incluyas texto fuera del JSON.
Solo puedes usar estas operaciones: count_centers, sum, average, grouped_sum, grouped_count.
Campos numéricos permitidos para metric: {json.dumps(list(CHAT_METRICAS))}.
Campos permitidos para group_by y filters: {json.dumps(list(CHAT_COLUMNAS))}.
Devuelve exactamente estas claves: operation, metric, group_by, filters, limit.
Usa metric=null cuando la operación no lo requiera; group_by=null salvo operaciones agrupadas.
filters debe ser un objeto con cero o más filtros, por ejemplo {{"DEPARTAMENTO":"CAUCA"}}.
limit debe ser un entero entre 1 y 10. Si la pregunta no se puede resolver con estas operaciones, usa operation="unsupported".
Pregunta: {pregunta}"""
        generado = cliente.models.generate_content(
            model=modelo,
            contents=instruccion,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
        )
        plan = json.loads(generado.text)

        operacion = plan.get("operation")
        metric = plan.get("metric")
        group_by = plan.get("group_by")
        filtros = plan.get("filters") or {}
        limite = plan.get("limit", 5)
        if operacion not in {"count_centers", "sum", "average", "grouped_sum", "grouped_count"}:
            return jsonify({"success": True, "respuesta": "Puedo ayudarte con totales, promedios y comparaciones por departamento, municipio, estado o conectividad. Prueba con otra pregunta."})
        if not isinstance(filtros, dict) or any(k not in CHAT_COLUMNAS or not isinstance(v, str) for k, v in filtros.items()):
            raise ValueError("Filtros no permitidos")
        if operacion in {"sum", "average", "grouped_sum"} and metric not in CHAT_METRICAS:
            raise ValueError("Métrica no permitida")
        if operacion in {"grouped_sum", "grouped_count"} and group_by not in CHAT_COLUMNAS:
            raise ValueError("Agrupación no permitida")
        if not isinstance(limite, int) or isinstance(limite, bool):
            limite = 5
        limite = max(1, min(limite, 10))

        datos = preparar_datos()
        for columna, valor in filtros.items():
            valores = datos[columna].astype("string").str.casefold().str.strip()
            datos = datos[valores.eq(valor.strip().casefold())]

        if operacion == "count_centers":
            respuesta = f"Con los filtros indicados hay {len(datos):,} centros digitales.".replace(",", ".")
        elif operacion in {"sum", "average"}:
            serie = datos[metric].dropna()
            valor = serie.sum() if operacion == "sum" else (serie.mean() if len(serie) else 0)
            numero = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            respuesta = f"{('La suma' if operacion == 'sum' else 'El promedio')} de {CHAT_METRICAS[metric]} es {numero}."
        else:
            if operacion == "grouped_count":
                serie = datos.groupby(group_by, dropna=False).size().sort_values(ascending=False)
                etiqueta = "centros"
            else:
                serie = datos.groupby(group_by, dropna=False)[metric].sum().sort_values(ascending=False)
                etiqueta = CHAT_METRICAS[metric]
            filas = serie.head(limite)
            if filas.empty:
                respuesta = "No encontré registros que coincidan con esos filtros."
            else:
                renglones = [f"{nombre if pd.notna(nombre) else 'Sin información'}: {valor:,.2f}".replace(",", ".") for nombre, valor in filas.items()]
                respuesta = f"Resultados por {CHAT_COLUMNAS[group_by].lower()} ({etiqueta}):\n" + "\n".join(renglones)
        return jsonify({"success": True, "respuesta": respuesta})
    except Exception:
        app.logger.exception("Error al procesar una pregunta del chatbot")
        return jsonify({"success": False, "respuesta": "No pude procesar esa pregunta. Intenta reformularla."}), 502


@app.get("/graficas/<path:filename>")
def servir_grafica(filename: str):
    return send_from_directory(GRAFICAS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True)
