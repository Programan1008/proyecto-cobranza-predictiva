"""
generate_campanas.py — Generación sintética de la tabla CAMPAÑAS
=================================================================

Proyecto: Sistema de Análisis Predictivo para Cobranza Bancaria
Módulo:   Generador de datos sintéticos
Propósito: Genera campañas masivas de cobranza distribuidas a lo largo del
           periodo de 18 meses, con canal, fechas, segmento y tramo objetivo.

Salida: data/raw/campanas.csv

Datos exclusivamente SINTÉTICOS. No contienen información real ni sensible.
"""

import numpy as np
import pandas as pd

import config

# Número de campañas a lo largo de los 18 meses (aprox. 1-2 por mes).
N_CAMPANAS = 30

# Canales típicos de campañas masivas (subconjunto, sin "visita").
CANALES_CAMPANA = ["sms", "correo", "whatsapp", "telefonico"]

# Opciones de segmento y tramo objetivo (incluye "todos").
SEGMENTOS_OBJ = ["masivo", "preferente", "premium", "todos"]
TRAMOS_OBJ = ["1-30", "31-60", "61-90", "90+", "todos"]


def generar_campanas(semilla: int = config.SEMILLA) -> pd.DataFrame:
    """
    Genera las campañas de cobranza.

    Retorna
    -------
    pd.DataFrame
        Tabla de campañas.
    """
    np.random.seed(semilla)

    campana_id = np.arange(1, N_CAMPANAS + 1)

    canal = np.random.choice(CANALES_CAMPANA, size=N_CAMPANAS, p=[0.40, 0.25, 0.25, 0.10])
    segmento_objetivo = np.random.choice(SEGMENTOS_OBJ, size=N_CAMPANAS)
    tramo_objetivo = np.random.choice(TRAMOS_OBJ, size=N_CAMPANAS)

    # Fechas de inicio repartidas a lo largo del periodo de 18 meses.
    fecha_inicio_periodo = pd.to_datetime(config.FECHA_INICIO)
    fecha_fin_periodo = pd.to_datetime(config.FECHA_FIN)
    dias_periodo = (fecha_fin_periodo - fecha_inicio_periodo).days

    # Día de inicio aleatorio dentro del periodo (dejando margen para la duración).
    dia_inicio = np.random.randint(0, dias_periodo - 30, size=N_CAMPANAS)
    fecha_inicio = fecha_inicio_periodo + pd.to_timedelta(dia_inicio, unit="D")

    # Duración de cada campaña: entre 7 y 30 días.
    duracion = np.random.randint(7, 31, size=N_CAMPANAS)
    fecha_fin = fecha_inicio + pd.to_timedelta(duracion, unit="D")

    # Nombre descriptivo de la campaña.
    nombre_campana = [
        f"Campaña {canal[i].capitalize()} {fecha_inicio[i].strftime('%b%Y')}"
        for i in range(N_CAMPANAS)
    ]

    df = pd.DataFrame({
        "campana_id": campana_id,
        "nombre_campana": nombre_campana,
        "canal": canal,
        "fecha_inicio": fecha_inicio.date,
        "fecha_fin": fecha_fin.date,
        "segmento_objetivo": segmento_objetivo,
        "tramo_objetivo": tramo_objetivo,
    })
    return df


def main():
    """Genera las campañas y guarda en data/raw/campanas.csv."""
    try:
        df_campanas = generar_campanas()

        config.DIR_RAW.mkdir(parents=True, exist_ok=True)
        ruta_salida = config.ARCHIVOS["campanas"]
        df_campanas.to_csv(ruta_salida, index=False, encoding="utf-8")

        print(f"[OK] Campañas generadas: {len(df_campanas)}")
        print(f"[OK] Archivo guardado en: {ruta_salida}")
        print("\n--- Distribución por canal ---")
        print(df_campanas["canal"].value_counts())
        print("\n--- Primeras 5 filas ---")
        print(df_campanas.head())

    except Exception as error:
        print(f"[ERROR] Falló la generación de campañas: {error}")
        raise


if __name__ == "__main__":
    main()