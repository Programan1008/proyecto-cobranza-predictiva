"""
generate_creditos.py — Generación sintética de la tabla CREDITOS
=================================================================

Proyecto: Sistema de Análisis Predictivo para Cobranza Bancaria
Módulo:   Generador de datos sintéticos
Propósito: Genera los créditos de cada cliente. La mora NO es aleatoria pura:
           depende de la propensión latente del cliente (perfil de riesgo),
           lo que da realismo y permite que los modelos aprendan patrones.

Entrada: data/raw/clientes.csv (debe existir previamente)
Salida:  data/raw/creditos.csv

Datos exclusivamente SINTÉTICOS. No contienen información real ni sensible.
"""

import numpy as np
import pandas as pd

import config


def _calcular_propension(df_clientes: pd.DataFrame) -> np.ndarray:
    """
    Calcula la propensión de pago latente (0 a 1) de cada cliente, a partir
    de sus características y los pesos definidos en config.py.

    Mayor propensión = cliente más cumplidor = menor mora esperada.
    """
    n = len(df_clientes)

    # Normalizar ingreso a [0, 1] (min-max) para que sea comparable.
    ingreso = df_clientes["ingreso_estimado"].to_numpy()
    ingreso_norm = (ingreso - ingreso.min()) / (ingreso.max() - ingreso.min())

    # Normalizar antigüedad a [0, 1].
    antig = df_clientes["antiguedad_cliente"].to_numpy()
    antig_norm = (antig - antig.min()) / (antig.max() - antig.min())

    # Factor "historial": aún no tenemos historial real (es el primer dato),
    # así que usamos un componente aleatorio que representa el perfil de base.
    historial = np.random.beta(2, 2, size=n)  # valores centrados en 0.5

    # Fórmula de propensión latente (ver config.py sección 5).
    propension = (
        config.PROPENSION_BASE
        + config.W_INGRESO * ingreso_norm
        + config.W_HISTORIAL * historial
        + config.W_ANTIGUEDAD * antig_norm
    )

    # Ruido aleatorio gaussiano (deliberado, para realismo).
    propension += np.random.normal(0, config.RUIDO_PROPENSION, size=n)

    # Recortar al rango válido [0, 1].
    return np.clip(propension, 0.0, 1.0)


def _cuota_francesa(monto: np.ndarray, tasa_anual: np.ndarray,
                    plazo: np.ndarray) -> np.ndarray:
    """
    Calcula la cuota mensual por el sistema de amortización francés.
    cuota = P * [ i(1+i)^n ] / [ (1+i)^n - 1 ]
    donde i = tasa mensual, n = plazo en meses.
    """
    i = tasa_anual / 12.0                 # tasa mensual
    factor = (1 + i) ** plazo
    cuota = monto * (i * factor) / (factor - 1)
    return np.round(cuota, 0)


def _dias_a_tramo(dias: int) -> str:
    """Convierte días de mora a su tramo (regla de coherencia del diccionario)."""
    if dias == 0:
        return "al_dia"
    elif dias <= 30:
        return "1-30"
    elif dias <= 60:
        return "31-60"
    elif dias <= 90:
        return "61-90"
    else:
        return "90+"


def generar_creditos(df_clientes: pd.DataFrame,
                     semilla: int = config.SEMILLA) -> pd.DataFrame:
    """
    Genera los créditos de todos los clientes.

    Parámetros
    ----------
    df_clientes : pd.DataFrame
        Tabla de clientes (necesaria para la relación FK y la propensión).
    semilla : int
        Semilla aleatoria.

    Retorna
    -------
    pd.DataFrame
        Tabla de créditos generados.
    """
    np.random.seed(semilla)

    # Propensión latente por cliente (la usaremos para la mora).
    propension_cliente = _calcular_propension(df_clientes)

    # --- Decidir cuántos créditos tiene cada cliente ---
    n_opciones = list(config.DIST_N_CREDITOS.keys())     # [1, 2, 3]
    n_probs = list(config.DIST_N_CREDITOS.values())      # [0.65, 0.27, 0.08]
    creditos_por_cliente = np.random.choice(
        n_opciones, size=len(df_clientes), p=n_probs
    )

    # Construir, para cada crédito, el cliente_id y la propensión asociada.
    cliente_ids = df_clientes["cliente_id"].to_numpy()
    fila_cliente_id = np.repeat(cliente_ids, creditos_por_cliente)
    fila_propension = np.repeat(propension_cliente, creditos_por_cliente)
    total_creditos = len(fila_cliente_id)

    # --- Atributos del crédito (vectorizado) ---
    credito_id = np.arange(1, total_creditos + 1)

    tipos = list(config.DIST_TIPO_CREDITO.keys())
    tipos_probs = list(config.DIST_TIPO_CREDITO.values())
    tipo_credito = np.random.choice(tipos, size=total_creditos, p=tipos_probs)

    monto_original = np.random.randint(
        config.MONTO_CREDITO_MIN, config.MONTO_CREDITO_MAX, size=total_creditos
    ).astype(float)

    tasa_interes = np.round(
        np.random.uniform(config.TASA_MIN, config.TASA_MAX, size=total_creditos), 3
    )

    plazo_meses = np.random.choice([6, 12, 18, 24, 36, 48, 60, 72], size=total_creditos)

    cuota_mensual = _cuota_francesa(monto_original, tasa_interes, plazo_meses)

    # --- Asignar mora según propensión latente ---
    # Calibramos la probabilidad de mora para que el PROMEDIO coincida con
    # PROP_EN_MORA, manteniendo que los clientes de baja propensión caigan más.
    # Centramos (1 - propension) en su media y lo escalamos al objetivo.
    riesgo = (1 - fila_propension)
    prob_mora = config.PROP_EN_MORA * (riesgo / riesgo.mean())
    prob_mora = np.clip(prob_mora, 0.0, 1.0)
    en_mora = np.random.random(total_creditos) < prob_mora

    # Días de mora: 0 si no está en mora; si lo está, la severidad depende de
    # la propensión (peor perfil => mora más profunda). Usamos una distribución
    # exponencial (sesgada a valores bajos) para reflejar una cartera realista:
    # muchos clientes en mora leve, pocos en mora profunda (forma de pirámide).
    dias_mora = np.zeros(total_creditos, dtype=int)
    idx_mora = np.where(en_mora)[0]
    severidad = (1 - fila_propension[idx_mora])  # 0 a 1, mayor = peor
    # Exponencial: la mayoría de valores son pequeños; la cola llega a 90+.
    # La escala media sube con la severidad del cliente (peor perfil, más días).
    escala = 25 + severidad * 70  # escala media entre 25 y 95 días
    dias_base = np.random.exponential(scale=escala, size=len(idx_mora))
    dias_mora[idx_mora] = np.clip(1 + dias_base, 1, 360).astype(int)

    # --- Saldo de deuda: proporción del monto original aún adeudada ---
    proporcion_saldo = np.random.uniform(0.2, 1.0, size=total_creditos)
    saldo_deuda = np.round(monto_original * proporcion_saldo, 0)

    # --- Derivar tramo y estado (coherencia) ---
    tramo_mora = np.array([_dias_a_tramo(d) for d in dias_mora])
    estado_credito = np.where(dias_mora == 0, "vigente", "moroso")
    # Mora muy profunda (>180) se considera candidata a castigo.
    estado_credito = np.where(dias_mora > 180, "castigado", estado_credito)

    # --- Fecha de originación: hasta 5 años atrás del inicio del periodo ---
    dias_atras = np.random.randint(30, 5 * 365, size=total_creditos)
    fecha_inicio = pd.to_datetime(config.FECHA_INICIO)
    fecha_originacion = fecha_inicio - pd.to_timedelta(dias_atras, unit="D")

    # --- Ensamblar ---
    df = pd.DataFrame({
        "credito_id": credito_id,
        "cliente_id": fila_cliente_id,
        "tipo_credito": tipo_credito,
        "monto_original": monto_original.astype(int),
        "saldo_deuda": saldo_deuda.astype(int),
        "tasa_interes": tasa_interes,
        "fecha_originacion": fecha_originacion.date,
        "plazo_meses": plazo_meses,
        "cuota_mensual": cuota_mensual.astype(int),
        "dias_mora": dias_mora,
        "tramo_mora": tramo_mora,
        "estado_credito": estado_credito,
    })
    return df


def main():
    """Carga clientes, genera créditos y guarda en data/raw/creditos.csv."""
    try:
        # Verificar que exista el archivo de clientes (dependencia).
        ruta_clientes = config.ARCHIVOS["clientes"]
        if not ruta_clientes.exists():
            raise FileNotFoundError(
                f"No existe {ruta_clientes}. Ejecuta primero generate_clientes.py"
            )

        df_clientes = pd.read_csv(ruta_clientes)
        df_creditos = generar_creditos(df_clientes)

        config.DIR_RAW.mkdir(parents=True, exist_ok=True)
        ruta_salida = config.ARCHIVOS["creditos"]
        df_creditos.to_csv(ruta_salida, index=False, encoding="utf-8")

        # Reporte de validación.
        print(f"[OK] Créditos generados: {len(df_creditos):,}")
        print(f"[OK] Archivo guardado en: {ruta_salida}")
        print(f"\n--- Créditos por cliente (promedio): "
              f"{len(df_creditos)/len(df_clientes):.2f} ---")
        print("\n--- Distribución por tramo de mora ---")
        print(df_creditos["tramo_mora"].value_counts(normalize=True).round(3))
        print("\n--- Distribución por estado ---")
        print(df_creditos["estado_credito"].value_counts(normalize=True).round(3))
        print("\n--- Primeras 5 filas ---")
        print(df_creditos.head())

    except Exception as error:
        print(f"[ERROR] Falló la generación de créditos: {error}")
        raise


if __name__ == "__main__":
    main()