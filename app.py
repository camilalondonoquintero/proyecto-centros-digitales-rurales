from pathlib import Path
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

from graficas import cargar_datos


BASE_DIR = Path(__file__).resolve().parent
GRAFICAS_DIR = BASE_DIR / "graficas"
app = Flask(__name__)


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


@app.get("/graficas/<path:filename>")
def servir_grafica(filename: str):
    return send_from_directory(GRAFICAS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True)
