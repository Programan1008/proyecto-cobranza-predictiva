"""
generate_clientes.py — Generación sintética de la tabla CLIENTES
=================================================================

Proyecto: Sistema de Análisis Predictivo para Cobranza Bancaria
Módulo:   Generador de datos sintéticos
Propósito: Genera 10.000 clientes sintéticos respetando las distribuciones
           definidas en config.py (segmento, ingreso, edad, región, etc.).

Salida: data/raw/clientes.csv

Datos exclusivamente SINTÉTICOS. No contienen información real ni sensible.
"""

import numpy as np
import pandas as pd
from faker import Faker

# Importamos los parámetros centrales desde config.py (misma carpeta).
import config


def generar_clientes(n_clientes: int = config.N_CLIENTES,
                     semilla: int = config.SEMILLA) -> pd.DataFrame:
    """
    Genera una tabla de clientes sintéticos.

    Parámetros
    ----------
    n_clientes : int
        Número de clientes a generar (por defecto, el de config.py).
    semilla : int
        Semilla aleatoria para reproducibilidad.

    Retorna
    -------
    pd.DataFrame
        DataFrame con los clientes generados.
    """
    # --- 1. Fijar la semilla (reproducibilidad) ---
    # Con la misma semilla, NumPy y Faker producen siempre los mismos datos.
    np.random.seed(semilla)
    faker = Faker(config.LOCALE_FAKER)
    Faker.seed(semilla)

    # --- 2. Generar cada columna de forma vectorizada ---

    # Identificador único: 1, 2, 3, ..., n_clientes.
    cliente_id = np.arange(1, n_clientes + 1)

    # Edad: enteros uniformes entre EDAD_MIN y EDAD_MAX (inclusive).
    edad = np.random.randint(config.EDAD_MIN, config.EDAD_MAX + 1, size=n_clientes)

    # Género: sorteo con probabilidades (mayoría F/M, pocos "Otro").
    genero = np.random.choice(config.GENEROS, size=n_clientes, p=[0.49, 0.49, 0.02])

    # Región: sorteo uniforme entre las 16 regiones de Chile.
    region = np.random.choice(config.REGIONES_CHILE, size=n_clientes)

    # Nivel de ingreso: respeta la distribución definida (45% bajo, 40% medio, 15% alto).
    niveles = list(config.DIST_NIVEL_INGRESO.keys())
    probs_nivel = list(config.DIST_NIVEL_INGRESO.values())
    nivel_ingreso = np.random.choice(niveles, size=n_clientes, p=probs_nivel)

    # Ingreso estimado: COHERENTE con el nivel. Para cada cliente, se sortea
    # un monto dentro del rango correspondiente a su nivel de ingreso.
    ingreso_estimado = np.zeros(n_clientes)
    for nivel, (minimo, maximo) in config.RANGO_INGRESO.items():
        # Máscara booleana: True en las posiciones de clientes de este nivel.
        mascara = (nivel_ingreso == nivel)
        # Cuántos clientes hay de este nivel.
        cuantos = mascara.sum()
        # Generamos esa cantidad de ingresos dentro del rango y los asignamos.
        ingreso_estimado[mascara] = np.random.randint(minimo, maximo, size=cuantos)

    # Segmento comercial: respeta la distribución (70% masivo, 22% pref., 8% premium).
    segmentos = list(config.DIST_SEGMENTO.keys())
    probs_seg = list(config.DIST_SEGMENTO.values())
    segmento = np.random.choice(segmentos, size=n_clientes, p=probs_seg)

    # Antigüedad como cliente (meses): entero uniforme en el rango.
    antiguedad_cliente = np.random.randint(
        config.ANTIGUEDAD_MIN, config.ANTIGUEDAD_MAX + 1, size=n_clientes
    )

    # Nombre sintético (Faker). Se genera en bucle porque Faker no es vectorizable.
    nombres = [faker.name() for _ in range(n_clientes)]

    # ejecutivo_id: se asigna NULL por ahora; se completará al generar gestiones.
    ejecutivo_id = np.full(n_clientes, np.nan)

    # --- 3. Ensamblar el DataFrame ---
    df = pd.DataFrame({
        "cliente_id": cliente_id,
        "nombre": nombres,
        "edad": edad,
        "genero": genero,
        "region": region,
        "nivel_ingreso": nivel_ingreso,
        "ingreso_estimado": ingreso_estimado.astype(int),
        "antiguedad_cliente": antiguedad_cliente,
        "segmento": segmento,
        "ejecutivo_id": ejecutivo_id,
    })

    return df


def main():
    """Genera los clientes y los guarda en data/raw/clientes.csv."""
    try:
        # Asegurar que la carpeta de salida exista.
        config.DIR_RAW.mkdir(parents=True, exist_ok=True)

        # Generar los clientes.
        df_clientes = generar_clientes()

        # Guardar a CSV (sin la columna de índice de Pandas).
        ruta_salida = config.ARCHIVOS["clientes"]
        df_clientes.to_csv(ruta_salida, index=False, encoding="utf-8")

        # Reporte de validación rápida en consola.
        print(f"[OK] Clientes generados: {len(df_clientes):,}")
        print(f"[OK] Archivo guardado en: {ruta_salida}")
        print("\n--- Distribución por segmento ---")
        print(df_clientes["segmento"].value_counts(normalize=True).round(3))
        print("\n--- Distribución por nivel de ingreso ---")
        print(df_clientes["nivel_ingreso"].value_counts(normalize=True).round(3))
        print("\n--- Primeras 5 filas ---")
        print(df_clientes.head())

    except Exception as error:
        print(f"[ERROR] Falló la generación de clientes: {error}")
        raise


if __name__ == "__main__":
    main()