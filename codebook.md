# Codebook — Laboratorio 4: Datos Geoespaciales

## Fuente de los datos

- **Colección:** `SENTINEL2_L2A` (reflectancia de superficie, corrección atmosférica)
- **Acceso:** API openEO de [Copernicus Data Space](https://dataspace.copernicus.eu) (`openeo.dataspace.copernicus.eu`)
- **Resolución espacial:** 10–20 m según banda
- **Fechas:** exclusivamente las 11 fechas oficiales por lago dadas en el enunciado (Amatitlán 2026-02-07 tiene cobertura parcial ~57.1%)

## Áreas de interés (bbox, EPSG:4326)

| Lago | west | east | south | north |
|---|---|---|---|---|
| Atitlán | -91.326256 | -91.07151 | 14.5948 | 14.750979 |
| Amatitlán | -90.638065 | -90.512924 | 14.412347 | 14.493799 |

GeoJSON generados en `data/raw/geojson/`.

## Bandas descargadas (`data/raw/<lago>/<fecha>.nc`)

| Variable | Tipo | Longitud de onda | Uso |
|---|---|---|---|
| B03 | float, reflectancia | 560 nm (verde) | NDWI, máscara de agua |
| B04 | float, reflectancia | 665 nm (rojo) | NDVI, NDCI |
| B05 | float, reflectancia | 705 nm (red edge) | NDCI (cianobacteria) |
| B08 | float, reflectancia | 842 nm (NIR) | NDVI, NDWI |
| SCL | entero categórico | — | clasificación de escena (6 = agua) |

## Variables derivadas (`data/processed/indices/<lago>/<fecha>.nc`)

| Variable | Fórmula | Rango | Interpretación |
|---|---|---|---|
| ndvi | (B08−B04)/(B08+B04) | [−1, 1] | vegetación; sobre agua suele ser < 0 |
| ndwi | (B03−B08)/(B03+B08) | [−1, 1] | agua abierta si > 0 |
| cyano | (B05−B04)/(B05+B04) — NDCI | [−1, 1] | clorofila-a / cianobacteria; solo definida sobre agua (NaN fuera del lago). Reproduce el Cyano Detection Script de custom-scripts.sentinel-hub.com |
| agua | booleana | 0/1 | SCL==6 ∨ NDWI>0.2 |

## Resumen tabular (`data/processed/resumen_indices.csv`)

| Columna | Tipo | Descripción |
|---|---|---|
| lago | str | `atitlan` / `amatitlan` |
| fecha | str ISO | fecha de la escena |
| {cyano,ndvi,ndwi}_media / _mediana / _p90 / _max | float | estadísticas del índice dentro del lago |
| {…}_n_pixeles | int | píxeles válidos usados |
| pct_lago_alto | float % | porcentaje del lago con cyano > umbral (0.1) |

## Otras salidas

- `picos_floracion.csv` — fechas con cyano_media > media + 1σ por lago
- `correlaciones.csv` — Pearson/Spearman por lago, fecha e índice
- `figuras/`, `mapas/` — PNGs y HTMLs de folium

## Transformaciones aplicadas

1. Recorte espacial al bbox de cada lago (server-side, openEO).
2. Selección de bandas mínimas (server-side) para minimizar descarga.
3. Máscara de agua (SCL==6 ∨ NDWI>0.2) antes de calcular el índice de cianobacteria.
4. Estadísticas ignoran NaN (píxeles fuera del lago o enmascarados).
