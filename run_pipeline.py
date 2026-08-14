"""Orquestador del pipeline del Laboratorio 4.

Uso:
    python run_pipeline.py            # corre todas las etapas
    python run_pipeline.py 02 03      # corre solo etapas específicas
"""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
ETAPAS = {
    "01": "01_descarga.py",
    "02": "02_indices.py",
    "03": "03_analisis_temporal.py",
    "04": "04_analisis_espacial.py",
    "05": "05_correlacion.py",
    "06": "06_exploratorio.py",
    "07": "07_comparativo.py",
}


def main():
    pedidas = sys.argv[1:] or list(ETAPAS)
    for etapa in pedidas:
        script = ETAPAS[etapa]
        print(f"\n{'=' * 60}\n>> Etapa {etapa}: {script}\n{'=' * 60}")
        subprocess.run([sys.executable, script], cwd=SRC, check=True)


if __name__ == "__main__":
    main()
