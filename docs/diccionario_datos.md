# Diccionario de Datos — Sistema de Análisis Predictivo para Cobranza Bancaria

**Versión:** 1.0
**Metodología:** CRISP-DM — Fase de Comprensión de Datos (Sprint 1)
**Naturaleza de los datos:** Sintéticos. No contienen información real ni sensible.

---

## Propósito de este documento

Este diccionario describe la estructura completa de la base de datos del proyecto:
cada tabla, cada campo, su tipo, su dominio de valores válidos y sus relaciones.
Es la fuente única de verdad sobre la cual se construye el generador de datos
sintéticos, el pipeline de Data Engineering y los modelos de Machine Learning.

## Convenciones

- **PK:** Clave primaria (identificador único de cada fila).
- **FK:** Clave foránea (referencia a la PK de otra tabla).
- **Nullable:** Indica si el campo admite valores vacíos (NULL).
- **Dominio:** Conjunto de valores permitidos para campos categóricos.

## Modelo de datos (resumen)

El modelo consta de 10 tablas organizadas en:

- **Dimensiones maestras:** CLIENTES, EJECUTIVOS, CAMPAÑAS
- **Entidad de crédito:** CREDITOS
- **Hechos (eventos):** PAGOS, GESTIONES, PROMESAS_PAGO, RENEGOCIACIONES, VISITAS
- **Tabla temporal (snapshots):** HISTORICO_CARTERA

Parámetros del proyecto: 10.000 clientes, 18 meses de historia, SQLite (migrable a PostgreSQL).

---

# GRUPO 1 — DIMENSIONES MAESTRAS

Entidades raíz del modelo. Existen de forma independiente y son referenciadas
por las demás tablas.

---

## Tabla: CLIENTES

Perfil demográfico y de relación de cada cliente con el banco. Es la dimensión
central del modelo: casi todas las tablas de hechos se relacionan con ella.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| cliente_id | INTEGER | PK | No | Identificador único del cliente | 1 a 10.000 |
| edad | INTEGER | | No | Edad del cliente en años | 18 a 80 |
| genero | TEXT | | No | Género del cliente | "F", "M", "Otro" |
| region | TEXT | | No | Región de residencia | 16 regiones de Chile |
| nivel_ingreso | TEXT | | No | Tramo de ingreso mensual | "bajo", "medio", "alto" |
| ingreso_estimado | REAL | | No | Ingreso mensual estimado (CLP) | 300.000 a 5.000.000 |
| antiguedad_cliente | INTEGER | | No | Meses desde que es cliente del banco | 1 a 360 |
| segmento | TEXT | | No | Segmento comercial del banco | "masivo", "preferente", "premium" |
| ejecutivo_id | INTEGER | FK | Sí | Ejecutivo de cobranza asignado | Ref. a EJECUTIVOS |

**Notas de diseño:**
- `ingreso_estimado` se correlaciona con `nivel_ingreso` (coherencia interna).
- `ejecutivo_id` es nullable porque un cliente sin mora puede no tener ejecutivo asignado.
- `region` permite análisis geográfico en el dashboard.

---

## Tabla: EJECUTIVOS

Gestores de cobranza que trabajan los casos. Permite analizar productividad
y carga operativa por persona.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| ejecutivo_id | INTEGER | PK | No | Identificador único del ejecutivo | 1 a N |
| nombre | TEXT | | No | Nombre del ejecutivo (sintético) | Generado con Faker |
| equipo | TEXT | | No | Equipo al que pertenece | "preventiva", "temprana", "tardia", "especializada" |
| productividad | REAL | | No | Índice de productividad histórica | 0.0 a 1.0 |
| carga_operativa | INTEGER | | No | N° de casos asignados actualmente | 0 a 300 |
| fecha_ingreso | DATE | | No | Fecha de ingreso del ejecutivo | Dentro del periodo |

**Notas de diseño:**
- `productividad` es un índice sintético: valores altos = gestor más efectivo.
- `carga_operativa` habilita el insight clave: "la efectividad cae cuando la carga supera cierto umbral".
- El número de ejecutivos se dimensiona según la carga (aprox. 1 ejecutivo por cada 100-150 clientes morosos).

---

## Tabla: CAMPAÑAS

Acciones masivas de cobranza dirigidas a grupos de clientes en un periodo.
Aportan contexto temporal y permiten medir su efecto sobre la recuperación.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| campaña_id | INTEGER | PK | No | Identificador único de la campaña | 1 a N |
| nombre_campaña | TEXT | | No | Nombre descriptivo de la campaña | Generado |
| canal | TEXT | | No | Canal principal de la campaña | "sms", "correo", "whatsapp", "telefonico" |
| fecha_inicio | DATE | | No | Fecha de inicio de la campaña | Dentro del periodo |
| fecha_fin | DATE | | No | Fecha de término de la campaña | >= fecha_inicio |
| segmento_objetivo | TEXT | | No | Segmento de clientes al que apunta | "masivo", "preferente", "premium", "todos" |
| tramo_objetivo | TEXT | | No | Tramo de mora objetivo | "1-30", "31-60", "61-90", "90+", "todos" |

**Notas de diseño:**
- Las campañas generan un efecto estacional sobre la recuperación (multiplicador temporal).
- `fecha_fin >= fecha_inicio` es una regla de coherencia a validar en la limpieza.
- Se generarán campañas distribuidas a lo largo de los 18 meses, con mayor intensidad en periodos clave (ej. fin de año).

---

# GRUPO 2 — ENTIDAD DE CRÉDITO

Conecta a cada cliente con sus productos de crédito. Es el nivel sobre el cual
ocurre la cobranza y donde residen la deuda, la mora y la base de los targets.

---

## Tabla: CREDITOS

Cada producto de crédito que un cliente tiene con el banco. Un cliente puede
tener múltiples créditos (relación 1:N desde CLIENTES).

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| credito_id | INTEGER | PK | No | Identificador único del crédito | 1 a N |
| cliente_id | INTEGER | FK | No | Cliente dueño del crédito | Ref. a CLIENTES |
| tipo_credito | TEXT | | No | Tipo de producto crediticio | "consumo", "tarjeta", "linea_credito" |
| monto_original | REAL | | No | Monto otorgado al inicio (CLP) | 200.000 a 30.000.000 |
| saldo_deuda | REAL | | No | Saldo adeudado actual (CLP) | 0 a monto_original |
| tasa_interes | REAL | | No | Tasa de interés anual del crédito | 0.10 a 0.45 |
| fecha_originacion | DATE | | No | Fecha en que se otorgó el crédito | Hasta 5 años atrás |
| plazo_meses | INTEGER | | No | Plazo total del crédito en meses | 6 a 72 |
| cuota_mensual | REAL | | No | Valor de la cuota mensual (CLP) | Derivado de monto/plazo/tasa |
| dias_mora | INTEGER | | No | Días de atraso actuales | 0 a 360 |
| tramo_mora | TEXT | | No | Tramo de mora actual (bucket) | "al_dia", "1-30", "31-60", "61-90", "90+" |
| estado_credito | TEXT | | No | Estado actual del crédito | "vigente", "moroso", "repactado", "castigado" |

**Notas de diseño:**

- **`monto_original` vs `saldo_deuda`:** el primero es fijo (lo prestado); el segundo es dinámico (lo que se debe hoy). El saldo nunca supera al monto original en este modelo simplificado.
- **`tasa_interes`** se expresa como decimal anual (0.25 = 25% anual). El rango refleja tasas de crédito de consumo/tarjeta en Chile.
- **`cuota_mensual`** es un campo derivado (calculado desde monto, plazo y tasa con fórmula de amortización). Se incluye precalculado para facilitar análisis.
- **`dias_mora` y `tramo_mora`** son redundantes a propósito: `dias_mora` es el número exacto, `tramo_mora` es su bucket. El bucket facilita agrupaciones; los días exactos permiten precisión. `tramo_mora` se deriva de `dias_mora` mediante una regla fija (regla de coherencia a validar).
- **`tramo_mora` aquí refleja el estado ACTUAL.** La evolución mensual de la mora se registra en la tabla HISTORICO_CARTERA (Grupo 4).
- **`estado_credito`** sigue el ciclo de vida: vigente (al día) → moroso (con atraso) → repactado (renegociado) o castigado (pérdida contable, mora 180+).

**Regla de coherencia tramo_mora ↔ dias_mora:**

| dias_mora | tramo_mora |
|-----------|------------|
| 0 | "al_dia" |
| 1 a 30 | "1-30" |
| 31 a 60 | "31-60" |
| 61 a 90 | "61-90" |
| 91 o más | "90+" |

---

# GRUPO 3 — TABLAS DE HECHOS (EVENTOS)

Registran eventos que ocurren en el tiempo (gestiones, pagos, promesas,
renegociaciones, visitas). Son las tablas de mayor volumen y donde residen
los targets de los modelos supervisados.

---

## Tabla: GESTIONES

Cada acción de cobranza realizada sobre un crédito. Es la tabla central de la
operación. Implementa la normalización de 5 dimensiones definida en Fase 0 v3.0.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| gestion_id | INTEGER | PK | No | Identificador único de la gestión | 1 a N |
| credito_id | INTEGER | FK | No | Crédito gestionado | Ref. a CREDITOS |
| cliente_id | INTEGER | FK | No | Cliente gestionado (denormalizado para análisis) | Ref. a CLIENTES |
| ejecutivo_id | INTEGER | FK | Sí | Ejecutivo que realizó la gestión | Ref. a EJECUTIVOS |
| campaña_id | INTEGER | FK | Sí | Campaña asociada (si aplica) | Ref. a CAMPAÑAS |
| fecha_gestion | DATE | | No | Fecha en que se realizó la gestión | Dentro del periodo (18 meses) |
| canal | TEXT | | No | Medio por el cual se gestionó | "telefonico", "whatsapp", "sms", "correo", "visita" |
| tipo_gestion | TEXT | | No | Propósito de la gestión | "primer_contacto", "seguimiento", "cobranza_preventiva", "cobranza_correctiva", "renegociacion", "recuperacion", "cobranza_especializada" |
| contacto | TEXT | | No | Si se logró contactar al titular | "efectivo", "no_efectivo" |
| resultado_gestion | TEXT | | No | Resultado agrupado (para modelado y KPIs) | "compromiso_pago", "cliente_indica_pago", "ingreso_insuficiente", "sin_exito", "derivado", "renegociacion", "compromiso_visita", "cargo_en_cuenta", "intencion_normalizar" |
| resultado_detalle | TEXT | | No | Código operacional detallado (trazabilidad) | Ver catálogo de 18 códigos abajo |
| dias_mora_gestion | INTEGER | | No | Días de mora del crédito al momento de la gestión | 0 a 360 |

**Catálogo de resultado_detalle (18 códigos operacionales) y su agrupación:**

| resultado_detalle | contacto | resultado_gestion (grupo) |
|-------------------|----------|---------------------------|
| contacto_efectivo | efectivo | (genérico) |
| compromiso_pago | efectivo | compromiso_pago |
| cliente_indica_pago | efectivo | cliente_indica_pago |
| intencion_normalizar | efectivo | intencion_normalizar |
| ingreso_insuficiente | efectivo | ingreso_insuficiente |
| sin_exito_comercial | efectivo | sin_exito |
| compromiso_visita | efectivo | compromiso_visita |
| renegociacion_online | efectivo | renegociacion |
| renegociacion_salesforce | efectivo | renegociacion |
| prce_online | efectivo | renegociacion |
| cargo_en_cuenta | efectivo | cargo_en_cuenta |
| derivado_equipo_empresa | efectivo | derivado |
| derivado_cdg | efectivo | derivado |
| derivado_banco | efectivo | derivado |
| no_contesta | no_efectivo | sin_exito |
| maquina_contestadora | no_efectivo | sin_exito |
| telefono_equivocado | no_efectivo | sin_exito |
| titular_corta_llamada | no_efectivo | sin_exito |

**Reglas de coherencia (a validar en la capa de limpieza):**

- Si `contacto = "no_efectivo"`, entonces `resultado_gestion` solo puede ser "sin_exito" o "derivado". No se puede obtener un compromiso de alguien con quien no se habló.
- Si `canal = "visita"`, la gestión debe tener un registro asociado en la tabla VISITAS.
- Si `resultado_gestion = "renegociacion"`, debe existir un registro en RENEGOCIACIONES.
- Si `resultado_gestion = "compromiso_pago"`, debe existir un registro en PROMESAS_PAGO.

**Notas de diseño:**

- `cliente_id` se incluye además de `credito_id` (denormalización deliberada) para acelerar análisis y joins en Power BI.
- `ejecutivo_id` y `campaña_id` son nullable: una gestión automática (SMS masivo) puede no tener ejecutivo; una gestión individual puede no pertenecer a campaña.
- `dias_mora_gestion` captura la mora EN EL MOMENTO de la gestión (no la actual), dato clave para evitar leakage temporal.

---

## Tabla: PROMESAS_PAGO

Registra cada promesa de pago que un cliente realiza durante una gestión.
Contiene el TARGET del Modelo 1 (cumplimiento de promesa de pago).

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| promesa_id | INTEGER | PK | No | Identificador único de la promesa | 1 a N |
| cliente_id | INTEGER | FK | No | Cliente que realiza la promesa | Ref. a CLIENTES |
| credito_id | INTEGER | FK | No | Crédito sobre el que se promete pagar | Ref. a CREDITOS |
| gestion_id | INTEGER | FK | Sí | Gestión en la que se originó la promesa | Ref. a GESTIONES |
| fecha_promesa | DATE | | No | Fecha en que se hizo la promesa | Dentro del periodo |
| monto_promesa | REAL | | No | Monto que el cliente promete pagar (CLP) | > 0 |
| fecha_compromiso | DATE | | No | Fecha en que promete pagar | >= fecha_promesa |
| monto_pagado | REAL | | No | Monto efectivamente pagado (CLP) | >= 0 |
| fecha_pago_real | DATE | | Sí | Fecha en que pagó (NULL si no pagó) | >= fecha_promesa o NULL |
| cumplida | BOOLEAN | | No | TARGET M1: si cumplió la promesa | 0 = no cumplió, 1 = cumplió |

**Definición del target `cumplida` (Opción B - con gracia):**

`cumplida = 1` si y solo si:
- `monto_pagado >= 0.90 * monto_promesa` (pagó al menos el 90% de lo prometido), Y
- `fecha_pago_real <= fecha_compromiso + 5 días hábiles` (dentro de la ventana de gracia)

En cualquier otro caso, `cumplida = 0`.

**Notas de diseño:**
- Se guardan los datos crudos (montos y fechas) además del flag calculado, para trazabilidad y poder recalcular el target con otra regla si se desea.
- `fecha_pago_real` es NULL cuando el cliente no pagó nada.
- La propensión a cumplir depende de las características del cliente (propensión latente + ruido + estacionalidad), según lógica de generación de Fase 0 v3.0.

---

## Tabla: RENEGOCIACIONES

Registra cada renegociación (repactación) de deuda. Contiene el TARGET del
Modelo 2 (renegociación exitosa).

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| renegociacion_id | INTEGER | PK | No | Identificador único de la renegociación | 1 a N |
| cliente_id | INTEGER | FK | No | Cliente que renegocia | Ref. a CLIENTES |
| credito_id | INTEGER | FK | No | Crédito renegociado | Ref. a CREDITOS |
| gestion_id | INTEGER | FK | Sí | Gestión en que se originó | Ref. a GESTIONES |
| tipo_renegociacion | TEXT | | No | Canal por el que se renegoció | "online", "ejecutiva" |
| fecha_renegociacion | DATE | | No | Fecha de la renegociación | Dentro del periodo |
| monto_renegociado | REAL | | No | Monto total reestructurado (CLP) | > 0 |
| cuotas | INTEGER | | No | N° de cuotas pactadas | 1 a 48 |
| cuotas_pagadas | INTEGER | | No | N° de cuotas efectivamente pagadas | 0 a cuotas |
| estado | TEXT | | No | Estado del ciclo de la renegociación | "abierta", "vigente", "exitosa", "caida" |
| renegociacion_exitosa | BOOLEAN | | No | TARGET M2: si la renegociación tuvo éxito | 0 = no, 1 = sí |

**Definición del target `renegociacion_exitosa` (Opción C - vigencia sostenida):**

`renegociacion_exitosa = 1` si y solo si:
- `cuotas_pagadas >= 3` (pagó al menos las 3 primeras cuotas del nuevo plan), lo que indica que la repactación se sostuvo.

En cualquier otro caso (caída antes de la 3ª cuota), `renegociacion_exitosa = 0`.

**Ciclo del campo `estado`:**
- `abierta`: recién pactada, sin cuotas pagadas aún.
- `vigente`: pagando, pero aún no llega a la 3ª cuota.
- `exitosa`: alcanzó el umbral de éxito (3+ cuotas).
- `caida`: dejó de pagar antes de consolidarse.

**Notas de diseño:**
- `tipo_renegociacion` distingue online (autoservicio, barato) de ejecutiva (gestor, caro). El Modelo 2 podrá recomendar el canal óptimo por cliente.
- El éxito depende de las características del cliente (propensión latente), enlazando con la lógica de generación de Fase 0 v3.0.
- Al crear una renegociación, el `estado_credito` del crédito asociado pasa a "repactado" (regla de coherencia).

---

## Tabla: PAGOS

Registra cada pago efectivo realizado sobre un crédito (provenga o no de una
promesa). Es la base contable real de la recuperación y fuente del target del
Modelo 3.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| pago_id | INTEGER | PK | No | Identificador único del pago | 1 a N |
| credito_id | INTEGER | FK | No | Crédito sobre el que se paga | Ref. a CREDITOS |
| cliente_id | INTEGER | FK | No | Cliente que paga (denormalizado) | Ref. a CLIENTES |
| promesa_id | INTEGER | FK | Sí | Promesa asociada (NULL si pago espontáneo) | Ref. a PROMESAS_PAGO |
| fecha_pago | DATE | | No | Fecha en que se realizó el pago | Dentro del periodo |
| monto_pago | REAL | | No | Monto pagado (CLP) | > 0 |
| tipo_pago | TEXT | | No | Origen / canal del pago | "normal", "promesa", "renegociacion", "cargo_automatico" |
| cumplido | BOOLEAN | | No | Si el pago corresponde a la cuota esperada del mes | 0 = parcial/atrasado, 1 = cuota cumplida |

**Notas de diseño:**
- `promesa_id` es nullable: hay pagos espontáneos sin promesa previa.
- `tipo_pago` distingue el origen del pago, útil para análisis de efectividad por estrategia.
- `cumplido` indica si el pago equivale a la cuota esperada del periodo (insumo de la feature `tendencia_pago`).
- La suma de pagos por crédito permite calcular la recuperación, base del target del Modelo 3 (definición del target se detalla en el sprint de modelado).

---

## Tabla: VISITAS

Registra las visitas a terreno realizadas (canal de cobranza más costoso).
Se asocia a gestiones de canal "visita". Señal de escalamiento del caso.

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| visita_id | INTEGER | PK | No | Identificador único de la visita | 1 a N |
| cliente_id | INTEGER | FK | No | Cliente visitado | Ref. a CLIENTES |
| credito_id | INTEGER | FK | No | Crédito objeto de la visita | Ref. a CREDITOS |
| gestion_id | INTEGER | FK | Sí | Gestión asociada a la visita | Ref. a GESTIONES |
| ejecutivo_id | INTEGER | FK | Sí | Ejecutivo que realizó la visita | Ref. a EJECUTIVOS |
| fecha_visita | DATE | | No | Fecha de la visita | Dentro del periodo |
| resultado_visita | TEXT | | No | Resultado de la visita a terreno | "ubicado_compromiso", "ubicado_sin_acuerdo", "no_ubicado", "domicilio_erroneo", "tercero_informa" |

**Notas de diseño:**
- Las visitas son el último recurso por su alto costo; su frecuencia es baja comparada con otros canales.
- `resultado_visita` tiene su propio dominio (distinto de resultado_gestion) porque la dinámica del terreno difiere de la gestión remota.
- "no_ubicado" y "domicilio_erroneo" son señales fuertes de riesgo (cliente "fantasma").
- Una visita implica una gestión asociada de canal "visita" (regla de coherencia).

---

# GRUPO 4 — TABLA TEMPORAL (SNAPSHOTS)

Captura el estado de cada crédito al cierre de cada mes. Es la columna vertebral
del análisis temporal, los KPIs históricos de Power BI y la generación de features
de Machine Learning. Diseño minimalista: almacena estados observados (hechos),
no métricas derivadas (estas se calculan en feature engineering).

---

## Tabla: HISTORICO_CARTERA

Una fila por cada crédito y por cada mes del periodo. Con 10.000 clientes y
18 meses, alcanza el orden de ~180.000 filas (según créditos activos por mes).

| Campo | Tipo | PK/FK | Nullable | Descripción | Dominio / Rango |
|-------|------|-------|----------|-------------|-----------------|
| snapshot_id | INTEGER | PK | No | Identificador único del snapshot | 1 a N |
| fecha_snapshot | DATE | | No | Último día del mes capturado | Cierre de cada mes (18 meses) |
| cliente_id | INTEGER | FK | No | Cliente del crédito | Ref. a CLIENTES |
| credito_id | INTEGER | FK | No | Crédito fotografiado | Ref. a CREDITOS |
| saldo_deuda | REAL | | No | Saldo adeudado al cierre del mes (CLP) | >= 0 |
| dias_mora | INTEGER | | No | Días de mora al cierre del mes | 0 a 360 |
| tramo_mora | TEXT | | No | Tramo de mora al cierre del mes | "al_dia", "1-30", "31-60", "61-90", "90+" |
| estado_credito | TEXT | | No | Estado del crédito al cierre del mes | "vigente", "moroso", "repactado", "castigado" |
| pagos_acumulados | REAL | | No | Suma de pagos del crédito DENTRO de ese mes (CLP) | >= 0 |
| score_riesgo_proxy | REAL | | No | Score de riesgo sintético del mes (0=bajo, 1=alto) | 0.0 a 1.0 |

**Notas de diseño:**

- **Granularidad:** una fila = un crédito en un mes. La combinación (credito_id, fecha_snapshot) es única.
- **`pagos_acumulados`:** corresponde a los pagos realizados DENTRO del mes del snapshot (no acumulado histórico total). Esto permite reconstruir series de pago mensuales sin ambigüedad. El acumulado histórico, si se necesita, se calcula sumando meses en feature engineering.
- **`score_riesgo_proxy`:** score sintético generado a partir de la lógica de propensión latente de Fase 0 v3.0 (NO es el output de un modelo entrenado). Se llama "proxy" para dejar explícito que es un valor sintético inicial. IMPORTANTE: no debe usarse como feature predictora de los modelos de riesgo, pues sería leakage (predecir el riesgo con un proxy del propio riesgo).
- **Orden de generación:** esta tabla se genera DESPUÉS de las transacciones (PAGOS, GESTIONES), porque resume su estado. Es una tabla derivada de los hechos, con test de cuadratura (el saldo debe ser coherente con los pagos registrados).

**Campos deliberadamente NO incluidos (se calculan en Feature Engineering):**

- variacion_mensual_deuda → resta entre saldo_deuda de meses consecutivos
- tendencia_pago → pendiente de regresión sobre pagos_acumulados recientes
- promedio_dias_mora → promedio de dias_mora sobre una ventana de meses
- roll rates → comparación de tramo_mora entre meses consecutivos

Razón: estos derivados dependen de la ventana temporal elegida y deben calcularse
con control de leakage (fecha de corte). Almacenarlos aquí duplicaría lógica y
restaría flexibilidad.

**Interacción con otros componentes:**

- **Feature Engineering:** fuente primaria de features temporales (variación, tendencia, promedios móviles), siempre filtrando fecha_snapshot < fecha_corte para evitar leakage.
- **EDA temporal:** evolución de cartera (GROUP BY fecha_snapshot), estacionalidad, distribución de tramos mes a mes.
- **Power BI:** roll rates (migración de tramos), evolución de saldo, score promedio mensual.
- **Modelos:** define la línea temporal que permite separar pasado (features) de futuro (target) sin contaminación.
