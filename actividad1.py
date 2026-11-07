import pandas as pd


datos = pd.read_csv("Centros_Digitales_Rurales_20260919.csv", encoding="utf-8-sig")

print("Primeras filas del archivo:")
print(datos.head())


datos.columns = datos.columns.str.strip()

for columna in datos.select_dtypes(include="object").columns:
	datos[columna] = datos[columna].str.strip()
	datos[columna] = datos[columna].replace("", pd.NA)

datos = datos.dropna(axis=1, how="all")
datos = datos.drop_duplicates()


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

datos["FECHA_CORTE"] = pd.to_datetime(datos["FECHA_CORTE"], errors="coerce")

print("\nInformación del archivo limpio:")
datos.info()

por_departamento = datos.groupby("DEPARTAMENTO").agg(
	centros=("MUNICIPIO", "count"),
	usuarios_activos=("USUARIOS_ACTIVOS_MES", "sum"),
	velocidad_promedio=("VELOCIDAD_CONEXION_BAJADA", "mean"),
)
print("\nCentros por departamento:")
print(por_departamento.sort_values("centros", ascending=False))


print("\nCentros por estado:")
print(datos.groupby("ESTADOS").size().sort_values(ascending=False))

print("\nCentros por tipo de conectividad:")
print(datos.groupby("TIPO_CONECTIVIDAD").size().sort_values(ascending=False))
