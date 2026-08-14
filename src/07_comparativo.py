"""Etapa 07 — Análisis y comparación entre lagos (ejercicio 7).

Reúne los índices de la etapa 02 en una tabla por lago y fecha, y compara los
dos lagos en intensidad y frecuencia de floración:
- Serie temporal del NDCI promedio de ambos lagos en un mismo eje (intensidad
  a lo largo del tiempo) -> data/processed/figuras/comparativo_lagos.png
- Barras de intensidad (NDCI promedio y pico) y de frecuencia (fracción de
  fechas en floración) por lago, en la misma figura.
- Tabla resumen por lago -> data/processed/comparacion_lagos.csv

Imprime las diferencias que sostienen la interpretación del ejercicio 7.

  python src/07_comparativo.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from config import DATA_PROCESSED, FIGURAS, LAGOS, UMBRAL_CIANO_ALTO

COLORES = {"atitlan": "#1f78b4", "amatitlan": "#e31a1c"}


def tabla_por_fecha() -> pd.DataFrame:
    """NDCI medio, máximo y % de agua alta por lago y fecha."""
    filas = []
    for clave, lago in LAGOS.items():
        for fecha in lago["fechas"]:
            ruta = DATA_PROCESSED / clave / f"{fecha}.nc"
            if not ruta.exists():
                continue
            v = xr.open_dataset(ruta)["cyano"].values
            v = v[np.isfinite(v)]
            if not v.size:
                continue
            filas.append({
                "lago": clave,
                "fecha": pd.Timestamp(fecha),
                "ndci_medio": float(v.mean()),
                "ndci_p90": float(np.percentile(v, 90)),
                "pct_alto": 100.0 * float(np.mean(v > UMBRAL_CIANO_ALTO)),
            })
    return pd.DataFrame(filas).sort_values(["lago", "fecha"]).reset_index(drop=True)


def resumen_por_lago(df: pd.DataFrame) -> pd.DataFrame:
    """Intensidad y frecuencia de floración resumidas por lago."""
    filas = []
    for clave, lago in LAGOS.items():
        sub = df[df["lago"] == clave]
        # una fecha "en floración" = NDCI medio del lago sobre el umbral
        frec_flor = 100.0 * float(np.mean(sub["ndci_medio"] > UMBRAL_CIANO_ALTO))
        filas.append({
            "lago": lago["nombre"],
            "ndci_medio": sub["ndci_medio"].mean(),
            "ndci_pico": sub["ndci_medio"].max(),
            "fecha_pico": sub.loc[sub["ndci_medio"].idxmax(), "fecha"].date(),
            "pct_agua_alto_medio": sub["pct_alto"].mean(),
            "frec_fechas_en_flor": frec_flor,
        })
    return pd.DataFrame(filas)


def figura_comparativa(df: pd.DataFrame, resumen: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                   gridspec_kw={"width_ratios": [1.6, 1]})

    # izquierda: serie temporal de ambos lagos
    for clave, lago in LAGOS.items():
        sub = df[df["lago"] == clave].sort_values("fecha")
        ax1.plot(sub["fecha"], sub["ndci_medio"], "-o", color=COLORES[clave],
                 label=lago["nombre"])
    ax1.axhline(UMBRAL_CIANO_ALTO, color="gray", ls=":", lw=1,
                label=f"umbral alto ({UMBRAL_CIANO_ALTO})")
    ax1.set_title("NDCI promedio a lo largo del tiempo")
    ax1.set_xlabel("fecha")
    ax1.set_ylabel("NDCI promedio sobre el agua")
    ax1.grid(alpha=0.3)
    ax1.legend()
    for etiqueta in ax1.get_xticklabels():
        etiqueta.set_rotation(30)
        etiqueta.set_ha("right")

    # derecha: intensidad (medio y pico) por lago
    x = np.arange(len(resumen))
    ancho = 0.35
    ax2.bar(x - ancho / 2, resumen["ndci_medio"], ancho, label="NDCI promedio",
            color=[COLORES[c] for c in LAGOS])
    ax2.bar(x + ancho / 2, resumen["ndci_pico"], ancho, label="NDCI pico",
            color=[COLORES[c] for c in LAGOS], alpha=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels([n.replace("Lago de ", "") for n in resumen["lago"]])
    ax2.axhline(UMBRAL_CIANO_ALTO, color="gray", ls=":", lw=1)
    ax2.set_title("Intensidad de floración por lago")
    ax2.set_ylabel("NDCI")
    ax2.legend()
    ax2.grid(alpha=0.3, axis="y")

    fig.suptitle("Comparación de cianobacteria entre lagos", fontsize=14)
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    salida = FIGURAS / "comparativo_lagos.png"
    fig.savefig(salida, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return salida


def main():
    df = tabla_por_fecha()
    if df.empty:
        print("⚠ sin índices procesados; correr antes 02_indices.py")
        return
    resumen = resumen_por_lago(df)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    csv = DATA_PROCESSED / "comparacion_lagos.csv"
    resumen.to_csv(csv, index=False)
    salida = figura_comparativa(df, resumen)
    print(f"✓ figura comparativa -> {salida.name}")
    print(f"✓ resumen por lago   -> {csv.name}\n")

    print(resumen.to_string(index=False))
    a, b = resumen.iloc[0], resumen.iloc[1]
    mas = a if a["ndci_medio"] > b["ndci_medio"] else b
    menos = b if mas is a else a
    # el NDCI promedio de un lago puede ser negativo (agua limpia), así que se
    # compara por diferencia y por frecuencia, no por un cociente
    print(f"\n{mas['lago']} es el más afectado: NDCI promedio {mas['ndci_medio']:+.3f} "
          f"frente a {menos['ndci_medio']:+.3f} del otro lago, con floración en el "
          f"{mas['frec_fechas_en_flor']:.0f}% de las fechas (contra "
          f"{menos['frec_fechas_en_flor']:.0f}%) y en promedio "
          f"{mas['pct_agua_alto_medio']:.0f}% del agua en floración por fecha.")


if __name__ == "__main__":
    main()
