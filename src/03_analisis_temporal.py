"""Etapa 03 — Análisis temporal del índice de cianobacteria (ejercicio 4).

Con los índices ya calculados en la etapa 02, resume la cianobacteria de cada
lago a un valor por fecha (índice promedio sobre el agua), grafica la evolución
temporal por lago, marca los picos de floración y reporta las fechas críticas.

  python src/03_analisis_temporal.py
"""
import glob

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from config import (DATA_PROCESSED, DATA_RAW, FIGURAS, LAGOS, UMBRAL_CIANO_ALTO)
from utils import calcular_indices, stats_por_fecha


def indices_de_fecha(clave: str, fecha: str) -> xr.Dataset:
    """Usa los índices de la etapa 02; si faltan, los recalcula de la escena."""
    procesado = DATA_PROCESSED / clave / f"{fecha}.nc"
    if procesado.exists():
        return xr.open_dataset(procesado)
    return calcular_indices(xr.open_dataset(DATA_RAW / clave / f"{fecha}.nc").squeeze(drop=True))


def fechas_de(clave: str):
    fuente = DATA_PROCESSED / clave
    if fuente.exists() and any(fuente.glob("*.nc")):
        rutas = sorted(fuente.glob("*.nc"))
    else:
        rutas = sorted(glob.glob(str(DATA_RAW / clave / "*.nc")))
    return [r.name.replace(".nc", "") if hasattr(r, "name") else r.split("/")[-1].replace(".nc", "")
            for r in rutas]


def resumen_lago(clave: str) -> pd.DataFrame:
    """Tabla con una fila por fecha: estadísticas del índice de cianobacteria."""
    filas = []
    for fecha in fechas_de(clave):
        idx = indices_de_fecha(clave, fecha)
        cyano = idx["cyano"]
        st = stats_por_fecha(cyano)
        vals = cyano.values[np.isfinite(cyano.values)]
        # porcentaje del agua con valores altos de cianobacteria (ejercicio 8.1)
        pct_alto = 100.0 * np.mean(vals > UMBRAL_CIANO_ALTO) if vals.size else np.nan
        filas.append({
            "lago": clave,
            "fecha": pd.Timestamp(fecha),
            "ndci_medio": st["media"],
            "ndci_mediana": st["mediana"],
            "ndci_p90": st["p90"],
            "ndci_max": st["max"],
            "pct_agua_alto": pct_alto,
            "px_agua": st["n_pixeles"],
        })
    return pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True)


def grafico_temporal(clave: str, lago: dict, df: pd.DataFrame):
    """Línea temporal del índice de cianobacteria del lago, con el pico marcado."""
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["fecha"], df["ndci_medio"], "-o", color="#2c7fb8", label="NDCI promedio")
    ax.plot(df["fecha"], df["ndci_p90"], "--s", color="#d95f0e", alpha=0.8,
            label="NDCI percentil 90")

    # pico de floración = fecha de mayor promedio
    i_pico = df["ndci_medio"].idxmax()
    f_pico, v_pico = df.loc[i_pico, "fecha"], df.loc[i_pico, "ndci_medio"]
    ax.scatter([f_pico], [v_pico], color="red", zorder=5, s=90)
    ax.annotate(f"pico {f_pico.date()}\n{v_pico:.3f}", (f_pico, v_pico),
                textcoords="offset points", xytext=(8, 10), color="red", fontsize=9)

    ax.axhline(UMBRAL_CIANO_ALTO, color="gray", ls=":", lw=1,
               label=f"umbral alto ({UMBRAL_CIANO_ALTO})")
    ax.set_title(f"Evolución del índice de cianobacteria — {lago['nombre']}")
    ax.set_xlabel("fecha")
    ax.set_ylabel("NDCI sobre el agua")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    salida = FIGURAS / f"temporal_{clave}.png"
    fig.savefig(salida, dpi=130)
    plt.close(fig)
    return salida


def comentar(clave: str, lago: dict, df: pd.DataFrame):
    """Imprime los hallazgos temporales: pico, mínimo y tendencia."""
    i_pico = df["ndci_medio"].idxmax()
    i_min = df["ndci_medio"].idxmin()
    pico, minimo = df.loc[i_pico], df.loc[i_min]
    # fechas críticas: por encima del promedio del lago más una desviación
    umbral = df["ndci_medio"].mean() + df["ndci_medio"].std()
    criticas = df[df["ndci_medio"] >= umbral]["fecha"].dt.date.tolist()
    tendencia = df["ndci_medio"].iloc[-1] - df["ndci_medio"].iloc[0]
    rumbo = "sube" if tendencia > 0.01 else "baja" if tendencia < -0.01 else "se mantiene"
    print(f"\n== {lago['nombre']} ==")
    print(f"  pico de floración: {pico['fecha'].date()} (NDCI medio {pico['ndci_medio']:.3f}, "
          f"{pico['pct_agua_alto']:.1f}% del agua con valores altos)")
    print(f"  mínimo:            {minimo['fecha'].date()} (NDCI medio {minimo['ndci_medio']:.3f})")
    print(f"  fechas críticas:   {criticas if criticas else 'ninguna sobre el umbral'}")
    print(f"  de inicio a fin el índice {rumbo} ({tendencia:+.3f})")


def main():
    tablas = []
    for clave, lago in LAGOS.items():
        df = resumen_lago(clave)
        tablas.append(df)
        salida = grafico_temporal(clave, lago, df)
        comentar(clave, lago, df)
        print(f"  ✓ gráfico temporal -> {salida.name}")

    completo = pd.concat(tablas, ignore_index=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    csv = DATA_PROCESSED / "temporal_cianobacteria.csv"
    completo.to_csv(csv, index=False)
    print(f"\nTabla temporal guardada en {csv}")


if __name__ == "__main__":
    main()
