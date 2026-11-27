# Centros Digitales Rurales

Aplicación web para explorar información de Centros Digitales Rurales en Colombia mediante indicadores, filtros, gráficos y estimaciones estadísticas.

## Funcionalidades

- Dashboard con centros registrados, usuarios activos, velocidad promedio de bajada e inversión.
- Filtros por departamento, estado y tipo de conectividad.
- API de resumen en `/api/resumen`.
- Chatbot opcional en `/api/chat`, conectado a Gemini para responder preguntas con operaciones permitidas sobre los datos.
- Gráficos descriptivos y proyecciones exploratorias por departamento.

## Requisitos

- Python 3.10 o superior.
- Dependencias listadas en `requirements.txt`.
- El archivo `Centros_Digitales_Rurales_20260919.csv` en la carpeta raíz del proyecto.

## Instalación y ejecución

Desde PowerShell, en la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python predicciones.py
python app.py
```

Abre `http://127.0.0.1:5000` en el navegador. `predicciones.py` genera los gráficos de regresión que utiliza el dashboard. Para generar los gráficos descriptivos adicionales, ejecuta:

```powershell
python graficas.py
```

## Chatbot (opcional)

El chatbot requiere una clave de Gemini. Crea un archivo local `.env` en la raíz y configura:

```dotenv
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-3.5-flash-lite
```

No compartas ni subas `.env` al repositorio. Sin `GEMINI_API_KEY`, el dashboard sigue disponible, pero el chatbot no responderá.

## Datos y estimaciones

El CSV es la fuente de datos. El proyecto limpia espacios y valores vacíos, elimina filas duplicadas y convierte algunas columnas numéricas y `FECHA_CORTE`. El dashboard muestra la fecha de corte más reciente disponible. Para conocer el rango completo de fechas, hay que revisar los valores de `FECHA_CORTE` del archivo.

Las estimaciones de `predicciones.py` usan regresiones lineales sobre agregados departamentales. No son una serie temporal ni una garantía de resultados futuros: deben tratarse como escenarios exploratorios y validarse antes de usarse para tomar decisiones.

## Archivos principales

| Archivo | Propósito |
| --- | --- |
| `app.py` | Aplicación Flask, dashboard, API y chatbot. |
| `graficas.py` | Limpieza de datos y generación de gráficos descriptivos. |
| `predicciones.py` | Cálculo de estimaciones y gráficos de regresión. |
| `Centros_Digitales_Rurales_20260919.csv` | Datos de centros digitales usados por la aplicación. |
| `templates/` y `static/` | Plantillas HTML, estilos y JavaScript del dashboard. |
| `requirements.txt` | Dependencias de Python. |

## Nota para despliegue

`app.py` inicia Flask con `debug=True`, adecuado solo para desarrollo local. Antes de desplegar en producción, desactiva el modo debug y configura el servidor y las credenciales de forma segura.
