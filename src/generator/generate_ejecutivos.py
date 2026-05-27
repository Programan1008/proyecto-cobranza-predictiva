"""
generate_ejecutivos.py — Generación sintética de la tabla EJECUTIVOS
=====================================================================

Proyecto: Sistema de Análisis Predictivo para Cobranza Bancaria
Módulo:   Generador de datos sintéticos
Propósito: Genera los ejecutivos (gestores) de cobranza. El número se dimensiona
           según el volumen de créditos en mora (realismo operacional).

Entrada: data/raw/creditos.csv (para dimensionar el equipo)
Salida:  data/raw/ejecutivos.csv

Datos exclusivamente SINTÉTICOS. No contienen información real ni sensible.
"""

import numpy as np
import pandas as pd
from faker import Faker

import config

# Cuántos casos en mora maneja, en promedio, un ejecutivo.
CASOS_POR_EJECUTIVO = 120


def generar_ejecutivos(n_creditos_mora: int,
                       semilla: int = config.SEMILLA) -> pd.DataFrame:
    """
    Genera los ejecutivos de cobranza.

    Parámetros
    ----------
    n_creditos_mora : int
        Número de créditos en mora (para dimensionar el equipo).
    semilla : int
        Semilla aleatoria.

    Retorna
    -------
    pd.DataFrame
        Tabla de ejecutivos.
    """
    np.random.seed(semilla)
    faker = Faker(config.LOCALE_FAKER)
    Faker.seed(semilla)

    # Dimensionar el equipo: al menos 10 ejecutivos, o los necesarios según carga.
    n_ejecutivos = max(10, int(np.ceil(n_creditos_mora / CASOS_POR_EJECUTIVO)))

    ejecutivo_id = np.arange(1, n_ejecutivos + 1)
    nombre = [faker.name() for _ in range(n_ejecutivos)]

    # Equipo: distribución por etapa de cobranza.
    equipo = np.random.choice(
        config.EQUIPOS, size=n_ejecutivos, p=[0.30, 0.35, 0.25, 0.10]
    )

    # Productividad: índice 0-1, distribución centrada (Beta) en torno a 0.6.
    productividad = np.round(np.random.beta(5, 3, size=n_ejecutivos), 3)

    # Carga operativa: número de casos asignados, variable por ejecutivo.
    carga_operativa = np.random.randint(50, 250, size=n_ejecutivos)

    # Fecha de ingreso: repartida en los últimos 5 años antes del periodo.
    dias_atras = np.random.randint(30, 5 * 365, size=n_ejecutivos)
    fecha_inicio = pd.to_datetime(config.FECHA_INICIO)
    fecha_ingreso = (fecha_inicio - pd.to_timedelta(dias_atras, unit="D")).date

    df = pd.DataFrame({
        "ejecutivo_id": ejecutivo_id,
        "nombre": nombre,
        "equipo": equipo,
        "productividad": productividad,
        "carga_operativa": carga_operativa,
        "fecha_ingreso": fecha_ingreso,
    })
    return df


def main():
    """Carga créditos para dimensionar, genera ejecutivos y guarda CSV."""
    try:
        ruta_creditos = config.ARCHIVOS["creditos"]
        if not ruta_creditos.exists():
            raise FileNotFoundError(
                f"No existe {ruta_creditos}. Ejecuta primero generate_creditos.py"
            )

        df_creditos = pd.read_csv(ruta_creditos)
        n_mora = int((df_creditos["estado_credito"] != "vigente").sum())

        df_ejecutivos = generar_ejecutivos(n_mora)

        config.DIR_RAW.mkdir(parents=True, exist_ok=True)
        ruta_salida = config.ARCHIVOS["ejecutivos"]
        df_ejecutivos.to_csv(ruta_salida, index=False, encoding="utf-8")

        print(f"[OK] Ejecutivos generados: {len(df_ejecutivos)}")
        print(f"[OK] Créditos en mora considerados: {n_mora:,}")
        print(f"[OK] Archivo guardado en: {ruta_salida}")
        print("\n--- Distribución por equipo ---")
        print(df_ejecutivos["equipo"].value_counts())
        print("\n--- Primeras 5 filas ---")
        print(df_ejecutivos.head())

    except Exception as error:
        print(f"[ERROR] Falló la generación de ejecutivos: {error}")
        raise


if __name__ == "__main__":
    main()