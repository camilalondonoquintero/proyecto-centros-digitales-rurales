
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


ARCHIVO = Path(__file__).with_name("Centros_Digitales_Rurales_20260919.csv")
CARPETA_GRAFICAS = Path(__file__).with_name("graficas")
datos = pd.read_csv(ARCHIVO, encoding="utf-8-sig", low_memory=False)
datos.columns = datos.columns.str.strip()

for columna in datos.select_dtypes(include="object").columns:
    datos[columna] = datos[columna].str.strip().replace("", pd.NA)

datos = datos.dropna(axis=1, how="all").drop_duplicates().copy()
datos["USUARIOS_ACTIVOS_MES"] = pd.to_numeric(
    datos["USUARIOS_ACTIVOS_MES"], errors="coerce"
)

print(f"Registros analizados: {len(datos):,}")
print(f"Fecha(s) de corte: {', '.join(datos['FECHA_CORTE'].dropna().unique())}")


def ajustar_regresion_lineal_simple(x, y):
    """Entrena una regresión lineal simple de y = intercepto + pendiente * x."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2 or np.ptp(x) == 0:
        raise ValueError("Se necesitan al menos dos valores distintos de x.")

    modelo = LinearRegression().fit(x.reshape(-1, 1), y)
    return modelo.intercept_, modelo.coef_[0], modelo.score(x.reshape(-1, 1), y), modelo


def guardar_grafica_regresion(
    x_observado,
    y_observado,
    modelo,
    x_predicciones,
    y_predicciones,
    titulo,
    etiqueta_x,
    etiqueta_y,
    archivo,
    etiquetas_predicciones,
):
    """Guarda una gráfica de puntos observados, tendencia y predicciones."""
    figura, eje = plt.subplots(figsize=(11, 6))
    x_observado = np.asarray(x_observado, dtype=float)
    y_observado = np.asarray(y_observado, dtype=float)
    x_predicciones = np.asarray(x_predicciones, dtype=float)
    y_predicciones = np.asarray(y_predicciones, dtype=float)

    eje.scatter(
        x_observado,
        y_observado,
        color="#9B8AC4",
        alpha=0.75,
        label="Datos observados",
    )
    x_linea = np.linspace(
        min(x_observado.min(), x_predicciones.min()),
        max(x_observado.max(), x_predicciones.max()),
        100,
    )
    eje.plot(
        x_linea,
        modelo.predict(x_linea.reshape(-1, 1)),
        color="#6750A4",
        linewidth=2,
        label="Línea de tendencia (modelo)",
    )
    eje.scatter(
        x_predicciones,
        y_predicciones,
        color="#FF8A65",
        edgecolors="#C94F4F",
        marker="*",
        s=150,
        label="Predicciones",
        zorder=3,
    )

    for x, y, etiqueta in zip(
        x_predicciones, y_predicciones, etiquetas_predicciones
    ):
        eje.annotate(
            etiqueta,
            (x, y),
            xytext=(5, 8),
            textcoords="offset points",
            fontsize=8,
        )

    eje.set_title(titulo)
    eje.set_xlabel(etiqueta_x)
    eje.set_ylabel(etiqueta_y)
    eje.grid(alpha=0.25)
    eje.set_axisbelow(True)
    eje.legend()
    figura.tight_layout()
    figura.savefig(CARPETA_GRAFICAS / archivo, dpi=160, bbox_inches="tight")
    plt.close(figura)


en_operacion = datos[datos["ESTADOS"].str.upper().eq("OPERACION")].copy()
sin_usuarios = en_operacion[en_operacion["USUARIOS_ACTIVOS_MES"].fillna(0).eq(0)].copy()

resumen_departamento = en_operacion.groupby("DEPARTAMENTO").agg(
    centros_operacion=("DEPARTAMENTO", "size"),
    usuarios_observados=("USUARIOS_ACTIVOS_MES", "sum"),
)
centros_con_usuarios = (
    en_operacion["USUARIOS_ACTIVOS_MES"].gt(0).groupby(en_operacion["DEPARTAMENTO"]).sum()
)
usuarios_activos = (
    en_operacion.loc[en_operacion["USUARIOS_ACTIVOS_MES"].gt(0)]
    .groupby("DEPARTAMENTO")["USUARIOS_ACTIVOS_MES"]
    .sum()
)
modelo_usuarios = resumen_departamento.loc[
    centros_con_usuarios.gt(0), ["centros_operacion"]
].copy()
modelo_usuarios["usuarios_observados"] = usuarios_activos
intercepto_usuarios, pendiente_usuarios, r2_usuarios, modelo_usuarios_regresion = ajustar_regresion_lineal_simple(
    modelo_usuarios["centros_operacion"], modelo_usuarios["usuarios_observados"]
)
usuarios_estimados_departamento = pd.Series(
    modelo_usuarios_regresion.predict(
        resumen_departamento["centros_operacion"].to_numpy().reshape(-1, 1)
    ),
    index=resumen_departamento.index,
).clip(lower=0)
centros_sin_usuarios = sin_usuarios.groupby("DEPARTAMENTO").size()
demanda_residual = (
    usuarios_estimados_departamento - resumen_departamento["usuarios_observados"]
).clip(lower=0)
sin_usuarios["USUARIOS_ESTIMADOS"] = (
    sin_usuarios["DEPARTAMENTO"]
    .map(demanda_residual / centros_sin_usuarios)
    .clip(lower=0)
)
print("\nPREDICCIÓN 1 — demanda potencial no observada")
print(f"Centros en operación con 0 usuarios reportados: {len(sin_usuarios):,}")
print(
    "Usuarios mensuales potenciales estimados (regresión lineal simple): "
    f"{sin_usuarios['USUARIOS_ESTIMADOS'].sum():,.0f}"
)
print(
    f"Modelo: usuarios = {intercepto_usuarios:.1f} + "
    f"{pendiente_usuarios:.1f} × centros operando (R²={r2_usuarios:.3f})"
)
print("Departamentos con más usuarios potenciales estimados:")
print(
    sin_usuarios.groupby("DEPARTAMENTO")["USUARIOS_ESTIMADOS"]
    .sum().sort_values(ascending=False).head(10).round(0).astype(int).to_string()
)
CARPETA_GRAFICAS.mkdir(exist_ok=True)
departamentos_destacados = (
    demanda_residual[demanda_residual.gt(0)]
    .sort_values(ascending=False)
    .head(10)
    .index
)
guardar_grafica_regresion(
    modelo_usuarios["centros_operacion"],
    modelo_usuarios["usuarios_observados"],
    modelo_usuarios_regresion,
    resumen_departamento.loc[departamentos_destacados, "centros_operacion"],
    usuarios_estimados_departamento.loc[departamentos_destacados],
    "Regresión lineal simple: usuarios activos por departamento",
    "Centros en operación",
    "Usuarios activos observados / estimados",
    "regresion_usuarios.png",
    departamentos_destacados,
)


conteo = datos.groupby("DEPARTAMENTO")["ESTADOS"].agg(
    total="size", operando=lambda s: s.str.upper().eq("OPERACION").sum()
)
pendientes = datos[datos["ESTADOS"].str.upper().isin(["INSTALACION", "PLANEACION"])]
pendientes_por_depto = pendientes.groupby("DEPARTAMENTO").size()
intercepto_operacion, pendiente_operacion, r2_operacion, modelo_operacion = ajustar_regresion_lineal_simple(
    conteo["total"], conteo["operando"]
)
operacion_proyectada = pd.Series(
    modelo_operacion.predict(conteo["total"].to_numpy().reshape(-1, 1)),
    index=conteo.index,
).clip(lower=0, upper=conteo["total"])
estimado_por_depto = (pendientes_por_depto * (
    operacion_proyectada / conteo["total"]
)).fillna(0)

print("\nPREDICCIÓN 2 — centros pendientes que podrían operar")
print(f"Centros en instalación o planeación: {len(pendientes):,}")
print(
    "Proyección con regresión lineal simple "
    f"(R²={r2_operacion:.3f}): {estimado_por_depto.sum():,.0f} centros"
)
print("Departamentos con mayor número estimado:")
print(estimado_por_depto.sort_values(ascending=False).head(10).round(1).to_string())
departamentos_destacados = estimado_por_depto.sort_values(ascending=False).head(10).index
guardar_grafica_regresion(
    conteo["total"],
    conteo["operando"],
    modelo_operacion,
    conteo.loc[departamentos_destacados, "total"],
    operacion_proyectada.loc[departamentos_destacados],
    "Regresión lineal simple: centros en operación",
    "Centros totales",
    "Centros operando observados / estimados",
    "regresion_operacion.png",
    departamentos_destacados,
)
print(f"\nGráficas guardadas en: {CARPETA_GRAFICAS}")

print(
    "\nNota: son estimaciones de referencia sobre una sola fecha de corte, "
    "no un pronóstico temporal. La regresión usa agregados por departamento; "
    "actualiza y valida con datos reales para medir su precisión."
)
