# Laboratorio 4 — Análisis de Datos Geoespaciales

CC3084 Data Science, UVG — Semestre II 2026.

Monitoreo de floraciones de **cianobacteria** en los lagos **Atitlán** y
**Amatitlán** con imágenes **Sentinel-2** (Copernicus), usando la API openEO
y los índices espectrales NDVI, NDWI y NDCI (índice de cianobacteria del
[Cyano Detection Script de Sentinel Hub](https://custom-scripts.sentinel-hub.com)).

## Estructura

```
lab4-ds/
├── src/                      # pipeline por etapas
│   ├── config.py             # bboxes, fechas oficiales, bandas, rutas
│   ├── utils.py              # índices, máscara de agua, geojson, stats
│   ├── 01_descarga.py        # openEO → data/raw/<lago>/<fecha>.nc
│   ├── 02_indices.py         # NDVI/NDWI/cyano → data/processed/indices/
│   ├── 03_analisis_temporal.py  # serie de tiempo + picos de floración
│   ├── 04_analisis_espacial.py  # mapas matplotlib + folium
│   ├── 05_correlacion.py     # NDVI/NDWI vs cianobacteria
│   └── 06_exploratorio.py    # persistencia, boxplots, estacionalidad
├── notebooks/                # exploración y armado del informe
├── data/raw/                 # .nc crudos por lago/fecha (no se modifican)
│   └── geojson/              # AOI de cada lago
├── data/processed/           # índices, CSVs, figuras, mapas (regenerable)
├── run_pipeline.py           # orquestador
├── requirements.txt
└── codebook.md
```

## Cómo correr todo de cero

Requiere cuenta gratuita en [Copernicus Data Space](https://dataspace.copernicus.eu)
(la etapa 01 abre el navegador para autenticarse).

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py          # o: python run_pipeline.py 02 03
```

**Windows:**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py
```

## Etapas del pipeline

1. **01_descarga** (ejercicios 1–2): conexión openEO y descarga de solo las
   bandas necesarias (B03, B04, B05, B08, SCL) recortadas al bbox de cada
   lago, únicamente en las 11 fechas oficiales por lago.
2. **02_indices** (ejercicio 3): NDVI, NDWI y NDCI (cianobacteria) por fecha,
   enmascarados al agua; genera `resumen_indices.csv`.
3. **03_analisis_temporal** (ejercicio 4): gráfico de línea por lago y
   detección de picos/fechas críticas.
4. **04_analisis_espacial** (ejercicio 5): paneles comparativos entre fechas
   y mapa interactivo folium por lago.
5. **05_correlacion** (ejercicio 6): Pearson/Spearman píxel a píxel y por
   medias de fecha.
6. **06_exploratorio** (ejercicio 8): % del lago con valores altos, zonas
   persistentes, boxplots por fecha y estacionalidad.

El análisis comparativo entre lagos (ejercicio 7) y las interpretaciones se
desarrollan en el informe a partir de las salidas de las etapas 3–6.

## Entregas

- **13 ago 2026 17:20** — avance: ejercicios 1 al 4.
- **16 ago 2026 23:59** — ejercicios completos + informe PDF (dirigido a
  ambientalistas sin conocimientos de programación).
