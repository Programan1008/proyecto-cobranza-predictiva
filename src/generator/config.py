"""
config.py — Parámetros centrales del generador de datos sintéticos
===================================================================

Proyecto: Sistema de Análisis Predictivo para Cobranza Bancaria
Módulo:   Generador de datos sintéticos
Propósito: Única fuente de verdad para todos los parámetros de generación.
           Toda la lógica de generación importa sus valores desde aquí.

Datos exclusivamente SINTÉTICOS. No contienen información real ni sensible.
"""

from pathlib import Path

# =============================================================================
# 1. PARÁMETROS GENERALES
# =============================================================================

# Semilla aleatoria: garantiza reproducibilidad. Con la misma semilla,
# el generador produce SIEMPRE los mismos datos.
SEMILLA = 42

# Volumen base de la simulación.
N_CLIENTES = 10_000        # Número de clientes a generar
MESES_HISTORIA = 18        # Meses de historia operacional

# Periodo temporal de la simulación (18 meses hacia atrás desde el cierre).
# El periodo termina al cierre del mes anterior al "hoy" de la simulación.
FECHA_INICIO = "2024-01-01"   # Primer mes del periodo simulado
FECHA_FIN = "2025-06-30"      # Último día del periodo (18 meses: ene-2024 a jun-2025)

# Moneda y locale (contexto chileno).
MONEDA = "CLP"
LOCALE_FAKER = "es_CL"        # Faker generará nombres/datos con formato chileno


# =============================================================================
# 2. RUTAS DE ARCHIVOS
# =============================================================================

# Raíz del proyecto: se calcula de forma robusta subiendo desde este archivo.
# config.py está en src/generator/, por lo que la raíz está 2 niveles arriba.
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

# Carpeta donde se guardan los datos crudos generados (capa "raw").
DIR_RAW = RAIZ_PROYECTO / "data" / "raw"

# Nombres de los archivos CSV de salida, uno por tabla.
ARCHIVOS = {
    "clientes": DIR_RAW / "clientes.csv",
    "ejecutivos": DIR_RAW / "ejecutivos.csv",
    "campanas": DIR_RAW / "campanas.csv",
    "creditos": DIR_RAW / "creditos.csv",
    "gestiones": DIR_RAW / "gestiones.csv",
    "promesas_pago": DIR_RAW / "promesas_pago.csv",
    "renegociaciones": DIR_RAW / "renegociaciones.csv",
    "pagos": DIR_RAW / "pagos.csv",
    "visitas": DIR_RAW / "visitas.csv",
    "historico_cartera": DIR_RAW / "historico_cartera.csv",
}


# =============================================================================
# 3. DOMINIOS / CATÁLOGOS (valores válidos, según el diccionario de datos)
# =============================================================================

# --- CLIENTES ---
GENEROS = ["F", "M", "Otro"]
NIVELES_INGRESO = ["bajo", "medio", "alto"]
SEGMENTOS = ["masivo", "preferente", "premium"]
REGIONES_CHILE = [
    "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo",
    "Valparaíso", "Metropolitana", "O'Higgins", "Maule", "Ñuble", "Biobío",
    "La Araucanía", "Los Ríos", "Los Lagos", "Aysén", "Magallanes",
]

# --- EJECUTIVOS ---
EQUIPOS = ["preventiva", "temprana", "tardia", "especializada"]

# --- CREDITOS ---
TIPOS_CREDITO = ["consumo", "tarjeta", "linea_credito"]
ESTADOS_CREDITO = ["vigente", "moroso", "repactado", "castigado"]
TRAMOS_MORA = ["al_dia", "1-30", "31-60", "61-90", "90+"]

# --- GESTIONES ---
CANALES = ["telefonico", "whatsapp", "sms", "correo", "visita"]
TIPOS_GESTION = [
    "primer_contacto", "seguimiento", "cobranza_preventiva",
    "cobranza_correctiva", "renegociacion", "recuperacion",
    "cobranza_especializada",
]
CONTACTO = ["efectivo", "no_efectivo"]
RESULTADOS_GESTION = [
    "compromiso_pago", "cliente_indica_pago", "ingreso_insuficiente",
    "sin_exito", "derivado", "renegociacion", "compromiso_visita",
    "cargo_en_cuenta", "intencion_normalizar",
]

# Catálogo de los 18 códigos detallados -> (contacto, resultado_gestion).
# Implementa la jerarquía de 3 niveles del diccionario (Fase 0 v3.0).
RESULTADO_DETALLE = {
    "contacto_efectivo":        ("efectivo", "sin_exito"),
    "compromiso_pago":          ("efectivo", "compromiso_pago"),
    "cliente_indica_pago":      ("efectivo", "cliente_indica_pago"),
    "intencion_normalizar":     ("efectivo", "intencion_normalizar"),
    "ingreso_insuficiente":     ("efectivo", "ingreso_insuficiente"),
    "sin_exito_comercial":      ("efectivo", "sin_exito"),
    "compromiso_visita":        ("efectivo", "compromiso_visita"),
    "renegociacion_online":     ("efectivo", "renegociacion"),
    "renegociacion_salesforce": ("efectivo", "renegociacion"),
    "prce_online":              ("efectivo", "renegociacion"),
    "cargo_en_cuenta":          ("efectivo", "cargo_en_cuenta"),
    "derivado_equipo_empresa":  ("efectivo", "derivado"),
    "derivado_cdg":             ("efectivo", "derivado"),
    "derivado_banco":           ("efectivo", "derivado"),
    "no_contesta":              ("no_efectivo", "sin_exito"),
    "maquina_contestadora":     ("no_efectivo", "sin_exito"),
    "telefono_equivocado":      ("no_efectivo", "sin_exito"),
    "titular_corta_llamada":    ("no_efectivo", "sin_exito"),
}

# --- RENEGOCIACIONES ---
TIPOS_RENEGOCIACION = ["online", "ejecutiva"]
ESTADOS_RENEGOCIACION = ["abierta", "vigente", "exitosa", "caida"]

# --- PAGOS ---
TIPOS_PAGO = ["normal", "promesa", "renegociacion", "cargo_automatico"]

# --- VISITAS ---
RESULTADOS_VISITA = [
    "ubicado_compromiso", "ubicado_sin_acuerdo", "no_ubicado",
    "domicilio_erroneo", "tercero_informa",
]


# =============================================================================
# 4. DISTRIBUCIONES Y PROBABILIDADES
# =============================================================================

# Proporción de clientes por segmento (deben sumar 1.0).
DIST_SEGMENTO = {"masivo": 0.70, "preferente": 0.22, "premium": 0.08}

# Proporción de clientes por nivel de ingreso (deben sumar 1.0).
DIST_NIVEL_INGRESO = {"bajo": 0.45, "medio": 0.40, "alto": 0.15}

# Rangos de ingreso mensual estimado (CLP) por nivel.
RANGO_INGRESO = {
    "bajo":  (300_000, 700_000),
    "medio": (700_000, 1_800_000),
    "alto":  (1_800_000, 5_000_000),
}

# Rango de edad de los clientes.
EDAD_MIN, EDAD_MAX = 18, 80

# Rango de antigüedad como cliente (en meses).
ANTIGUEDAD_MIN, ANTIGUEDAD_MAX = 1, 360

# Distribución de tipos de crédito.
DIST_TIPO_CREDITO = {"consumo": 0.50, "tarjeta": 0.35, "linea_credito": 0.15}

# Rango de monto original del crédito (CLP).
MONTO_CREDITO_MIN, MONTO_CREDITO_MAX = 200_000, 30_000_000

# Rango de tasa de interés anual (decimal).
TASA_MIN, TASA_MAX = 0.10, 0.45

# Número de créditos por cliente (probabilidades para 1, 2 o 3 créditos).
DIST_N_CREDITOS = {1: 0.65, 2: 0.27, 3: 0.08}

# Proporción de la cartera que está en mora (el resto está al día).
PROP_EN_MORA = 0.35


# =============================================================================
# 5. PESOS DE PROPENSIÓN LATENTE (corazón del realismo)
# =============================================================================
#
# Cada cliente recibe una "propensión de pago" oculta entre 0 y 1, calculada
# como combinación ponderada de sus características. Estos pesos definen cuánto
# influye cada factor. Signo (+) aumenta la propensión; signo (-) la disminuye.
#
# La fórmula conceptual es:
#   propension = BASE
#              + W_INGRESO * (ingreso normalizado)
#              + W_HISTORIAL * (buen historial)
#              + W_ANTIGUEDAD * (antiguedad normalizada)
#              - W_MORA * (mora normalizada)
#              - W_CONTACTO_FALLIDO * (contactos fallidos)
#              + ruido aleatorio
# El resultado se "recorta" al rango [0, 1].

PROPENSION_BASE = 0.50          # Punto de partida neutro

W_INGRESO = 0.20                # A mayor ingreso, mayor propensión de pago
W_HISTORIAL = 0.25              # Buen historial de cumplimiento sube propensión
W_ANTIGUEDAD = 0.10             # Clientes más antiguos pagan algo más
W_MORA = 0.30                   # A mayor mora, menor propensión (resta)
W_CONTACTO_FALLIDO = 0.15       # Contactos fallidos ("fantasma") restan

# Magnitud del ruido aleatorio (desviación estándar de un ruido gaussiano).
# Deliberado: evita un modelo "perfecto" e irreal. Calibra el realismo.
RUIDO_PROPENSION = 0.12


# =============================================================================
# 6. MULTIPLICADORES DE ESTACIONALIDAD (efectos por mes)
# =============================================================================
#
# Multiplican la propensión de pago o las tasas de contacto según el mes.
# Valor 1.0 = sin efecto; > 1.0 = aumenta; < 1.0 = disminuye.
# Claves: número de mes (1=enero, ..., 12=diciembre).

# Efecto estacional sobre la PROPENSIÓN DE PAGO.
ESTACIONALIDAD_PAGO = {
    1: 1.10,   # Enero: resaca de aguinaldo, aún hay liquidez
    2: 1.00,   # Febrero: normal
    3: 0.85,   # Marzo: gastos escolares, baja capacidad de pago
    4: 0.95, 5: 1.00, 6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00,
    11: 1.05,  # Noviembre: previo a fin de año
    12: 1.30,  # Diciembre: aguinaldo y bonos, sube el pago
}

# Efecto estacional sobre la TASA DE CONTACTO EFECTIVO.
ESTACIONALIDAD_CONTACTO = {
    1: 0.80,   # Enero: vacaciones, difícil contactar
    2: 0.80,   # Febrero: vacaciones
    3: 1.00, 4: 1.00, 5: 1.00, 6: 1.00, 7: 1.00, 8: 1.00,
    9: 1.00, 10: 1.00, 11: 1.00, 12: 1.00,
}

# Efecto multiplicador de una campaña activa sobre la recuperación.
EFECTO_CAMPANA = 1.20