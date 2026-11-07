from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).with_name(".matplotlib-cache")))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ARCHIVO_DATOS = Path(__file__).with_name("Centros_Digitales_Rurales_20260919.csv")
CARPETA_SALIDA = Path(__file__).with_name("graficas")
COLOR_PRINCIPAL = "#6750A4"


def cargar_datos() -> pd.DataFrame:
    datos = pd.read_csv(ARCHIVO_DATOS, encoding="utf-8-sig")
    datos.columns = datos.columns.str.strip()

    for columna in datos.select_dtypes(include=["object", "str"]).columns:
        datos[columna] = datos[columna].str.strip().replace("", pd.NA)

    datos = datos.dropna(axis=1, how="all").drop_duplicates()
    datos["FECHA_CORTE"] = pd.to_datetime(datos["FECHA_CORTE"], errors="coerce")
    columnas_numericas = [
        "USUARIOS_ACTIVOS_MES",
        "VELOCIDAD_CONEXION_SUBIDA",
        "VELOCIDAD_CONEXION_BAJADA",
        "TRAFICO_MENSUAL_SUBIDA",
        "TRAFICO_MENSUAL_BAJADA",
        "INVERSION",
    ]
    for columna in columnas_numericas:
        datos[columna] = pd.to_numeric(
            datos[columna].astype("string").str.replace(",", ".", regex=False),
            errors="coerce",
        )
    return datos


def guardar_barras(
    serie: pd.Series,
    titulo: str,
    eje_x: str,
    archivo: str,
    *,
    horizontal: bool = False,
) -> None:
    serie = serie.sort_values(ascending=horizontal)
    if horizontal:
        fig, ax = plt.subplots(figsize=(11, max(5, len(serie) * 0.38)))
        barras = ax.barh(serie.index.astype(str), serie.values, color=COLOR_PRINCIPAL)
        ax.bar_label(barras, padding=4, fmt="%.0f")
        ax.set_xlabel(eje_x)
        ax.invert_yaxis()
        ax.margins(x=0.12)
    else:
        fig, ax = plt.subplots(figsize=(11, 6))
        barras = ax.bar(serie.index.astype(str), serie.values, color=COLOR_PRINCIPAL)
        ax.bar_label(barras, padding=3, fmt="%.0f")
        ax.set_xlabel(eje_x)
        ax.set_ylabel("Cantidad de registros")
        ax.tick_params(axis="x", labelrotation=25)
        ax.margins(y=0.12)

    ax.set_title(titulo)
    ax.grid(axis="x" if horizontal else "y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(CARPETA_SALIDA / archivo, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    datos = cargar_datos()
    CARPETA_SALIDA.mkdir(exist_ok=True)

    registros_estado = datos["ESTADOS"].fillna("SIN INFORMACIÓN").value_counts()
    registros_conectividad = (
        datos["TIPO_CONECTIVIDAD"]
        .fillna("SIN INFORMACIÓN")
        .value_counts()
        .sort_values(ascending=False)
    )
    por_departamento = datos.groupby("DEPARTAMENTO").agg(
        centros=("MUNICIPIO", "count"),
        usuarios_activos=("USUARIOS_ACTIVOS_MES", "sum"),
        velocidad_promedio=("VELOCIDAD_CONEXION_BAJADA", "mean"),
    )

    guardar_barras(
        registros_estado,
        "Registros por estado",
        "Estado",
        "registros_por_estado.png",
    )
    guardar_barras(
        registros_conectividad,
        "Registros por tipo de conectividad",
        "Tipo de conectividad",
        "registros_por_conectividad.png",
        horizontal=True,
    )
    guardar_barras(
        por_departamento["centros"],
        "Centros por departamento",
        "Centros",
        "centros_por_departamento.png",
        horizontal=True,
    )
    guardar_barras(
        por_departamento["usuarios_activos"],
        "Usuarios activos por departamento",
        "Usuarios activos",
        "usuarios_activos_por_departamento.png",
        horizontal=True,
    )
    guardar_barras(
        por_departamento["velocidad_promedio"].dropna(),
        "Velocidad promedio de bajada por departamento",
        "Velocidad promedio de bajada",
        "velocidad_promedio_por_departamento.png",
        horizontal=True,
    )

    fecha = datos["FECHA_CORTE"].dropna().dt.strftime("%d/%m/%Y").unique()
    print(f"Fecha(s) de corte: {', '.join(fecha) if len(fecha) else 'sin dato'}")
    print(f"Registros analizados: {len(datos):,}")
    print(f"Departamentos analizados: {len(por_departamento)}")
    print(f"Gráficas guardadas en: {CARPETA_SALIDA}")


if __name__ == "__main__":
    main()
