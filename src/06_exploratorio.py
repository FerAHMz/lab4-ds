"""Etapa 06 — Análisis exploratorio adicional (ejercicio 8).

Sobre los índices de la etapa 02 explora, para cada lago:
- La extensión de la floración por fecha: porcentaje del agua con NDCI alto
  (ejercicio 8.1) -> data/processed/figuras/extension_alto.png
- Las zonas persistentes de acumulación: fracción de fechas en que cada píxel
  supera el umbral (ejercicio 8.2) -> data/processed/figuras/persistencia_<lago>.png
- La distribución del índice entre fechas con boxplots (ejercicio 8.3)
  -> data/processed/figuras/distribucion_<lago>.png
- El patrón estacional: NDCI promedio por mes (ejercicio 8.4)
  -> data/processed/figuras/estacional.png

Imprime un resumen que interpreta cada hallazgo (ejercicio 8.5).

  python src/06_exploratorio.py
"""
import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from config import DATA_PROCESSED, FIGURAS, LAGOS, UMBRAL_CIANO_ALTO

COLORES = {"atitlan": "#1f78b4", "amatitlan": "#e31a1c"}


def fechas_disponibles(clave: str, lago: dict):
    return [f for f in lago["fechas"]
            if (DATA_PROCESSED / clave / f"{f}.nc").exists()]


def cyano(clave: str, fecha: str) -> np.ndarray:
    return xr.open_dataset(DATA_PROCESSED / clave / f"{fecha}.nc")["cyano"].values


def extension_por_fecha(disp: dict) -> pd.DataFrame:
    """Porcentaje del agua con NDCI alto en cada fecha (ejercicio 8.1)."""
    filas = []
    for clave, fechas in disp.items():
        for fecha in fechas:
            v = cyano(clave, fecha)
            v = v[np.isfinite(v)]
            pct = 100.0 * np.mean(v > UMBRAL_CIANO_ALTO) if v.size else np.nan
            filas.append({"lago": clave, "fecha": pd.Timestamp(fecha), "pct_alto": pct})
    return pd.DataFrame(filas)


def grafico_extension(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 5))
    for clave, lago in LAGOS.items():
        sub = df[df["lago"] == clave].sort_values("fecha")
        ax.plot(sub["fecha"], sub["pct_alto"], "-o", color=COLORES[clave],
                label=lago["nombre"])
    ax.set_title("Extensión de la floración: % del agua con NDCI alto por fecha")
    ax.set_xlabel("fecha")
    ax.set_ylabel(f"% del agua con NDCI > {UMBRAL_CIANO_ALTO}")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    salida = FIGURAS / "extension_alto.png"
    fig.savefig(salida, dpi=130)
    plt.close(fig)
    return salida


def mapa_persistencia(clave: str, lago: dict, fechas: list):
    """Fracción de fechas en que cada píxel supera el umbral (ejercicio 8.2)."""
    alto = valido = None
    for fecha in fechas:
        v = cyano(clave, fecha)
        fin = np.isfinite(v)
        a = (v > UMBRAL_CIANO_ALTO) & fin
        alto = a.astype(float) if alto is None else alto + a
        valido = fin.astype(float) if valido is None else valido + fin
    with np.errstate(invalid="ignore", divide="ignore"):
        frec = np.where(valido > 0, alto / valido, np.nan)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(frec, cmap="inferno", vmin=0, vmax=1)
    ax.set_title(f"Zonas persistentes de cianobacteria — {lago['nombre']}")
    ax.set_xticks([])
    ax.set_yticks([])
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("fracción de fechas con NDCI alto")
    fig.tight_layout()
    salida = FIGURAS / f"persistencia_{clave}.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    # % del agua que es floración persistente (alto en >=50% de las fechas)
    persistente = 100.0 * np.nansum(frec >= 0.5) / max(np.sum(valido > 0), 1)
    return salida, persistente


def boxplots_distribucion(clave: str, lago: dict, fechas: list):
    """Distribución del NDCI sobre el agua en cada fecha (ejercicio 8.3)."""
    datos, etiquetas = [], []
    for fecha in fechas:
        v = cyano(clave, fecha)
        datos.append(v[np.isfinite(v)])
        etiquetas.append(fecha[5:])  # mm-dd
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.boxplot(datos, tick_labels=etiquetas, showfliers=False)
    ax.axhline(UMBRAL_CIANO_ALTO, color="red", ls=":", lw=1,
               label=f"umbral alto ({UMBRAL_CIANO_ALTO})")
    ax.set_title(f"Distribución del NDCI por fecha — {lago['nombre']}")
    ax.set_xlabel("fecha (mm-dd)")
    ax.set_ylabel("NDCI sobre el agua")
    ax.grid(alpha=0.3, axis="y")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    salida = FIGURAS / f"distribucion_{clave}.png"
    fig.savefig(salida, dpi=130)
    plt.close(fig)
    return salida


def grafico_estacional(disp: dict):
    """NDCI promedio por mes, para ver si hay patrón estacional (ejercicio 8.4)."""
    filas = []
    for clave, fechas in disp.items():
        for fecha in fechas:
            v = cyano(clave, fecha)
            filas.append({"lago": clave, "mes": int(fecha[5:7]),
                          "ndci": float(np.nanmean(v))})
    df = pd.DataFrame(filas)
    tabla = df.groupby(["lago", "mes"])["ndci"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    for clave, lago in LAGOS.items():
        sub = tabla[tabla["lago"] == clave].sort_values("mes")
        ax.plot(sub["mes"], sub["ndci"], "-o", color=COLORES[clave],
                label=lago["nombre"])
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([calendar.month_abbr[m] for m in range(1, 13)])
    ax.set_title("Patrón estacional: NDCI promedio por mes")
    ax.set_xlabel("mes")
    ax.set_ylabel("NDCI promedio sobre el agua")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    salida = FIGURAS / "estacional.png"
    fig.savefig(salida, dpi=130)
    plt.close(fig)
    return salida, df


def main():
    disp = {clave: fechas_disponibles(clave, lago) for clave, lago in LAGOS.items()}
    if not any(disp.values()):
        print("⚠ sin índices procesados; correr antes 02_indices.py")
        return

    ext = extension_por_fecha(disp)
    print("✓ extensión por fecha ->", grafico_extension(ext).name)

    for clave, lago in LAGOS.items():
        fechas = disp[clave]
        _, persistente = mapa_persistencia(clave, lago, fechas)
        boxplots_distribucion(clave, lago, fechas)
        media = ext[ext["lago"] == clave]["pct_alto"].mean()
        print(f"\n== {lago['nombre']} ==")
        print(f"  en promedio {media:.1f}% del agua está en floración por fecha")
        print(f"  {persistente:.1f}% del agua es floración persistente (alto en ≥50% de fechas)")

    _, estac = grafico_estacional(disp)
    print("\n✓ patrón estacional -> estacional.png")
    for clave, lago in LAGOS.items():
        sub = estac[estac["lago"] == clave]
        pico = sub.loc[sub["ndci"].idxmax()]
        print(f"  {lago['nombre']}: NDCI más alto en el mes {int(pico['mes'])} "
              f"({calendar.month_abbr[int(pico['mes'])]})")


if __name__ == "__main__":
    main()
