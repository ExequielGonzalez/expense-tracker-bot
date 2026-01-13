# Expense Tracker Bot

Bot de Telegram que analiza tickets de gastos mediante **OCR multi-engine** con sistema de fallback y reporta niveles de confianza.

## 🚀 Características

- 📷 Sube fotos de tickets
- 🔍 **Análisis multi-engine con fallback automático**
  - **Tesseract OCR** (rápido, bueno para texto claro)
  - **EasyOCR** (mejor con imágenes difíciles/borrosas)  
  - **PaddleOCR** (excelente para documentos estructurados) - opcional
- 💰 Extracción automática del monto con prioridad inteligente
- 🏪 Extracción del nombre del comercio/título
- 📅 Extracción de fechas con validación (años 2020-2030)
- 📂 **Clasificación automática de categoría mediante keywords**
- 🎯 **Reporta nivel de confianza (0-100%) para cada campo**
  - 🟢 80-100%: Alta confianza
  - 🟡 60-79%: Confianza media
  - 🔴 0-59%: Baja confianza - revisar manualmente
- 💾 Guardado en CSV con ruta a la foto
- 🖼️ Preservación de imágenes de los tickets
- ✅ Tests automatizados con validación de confianza

## 🎯 Sistema de Confianza

Cada campo extraído incluye un **score de confianza** (0-100%):

- 🟢 **80-100%**: Alta confianza - Datos muy confiables
- 🟡 **60-79%**: Confianza media - Revisar datos importantes
- 🔴 **0-59%**: Baja confianza - Verificar manualmente

**Confianza general**: Promedio ponderado de todos los campos
- Monto: 40% peso
- Fecha: 20% peso
- Título: 20% peso
- Categoría: 20% peso

## 🔧 Sistema Multi-Engine OCR

### Engines disponibles:

1. **Tesseract OCR** (rápido, bueno para texto claro)
2. **EasyOCR** (mejor con imágenes difíciles/borrosas)
3. **PaddleOCR** (excelente para documentos estructurados)

### Sistema de fallback:

El bot **prueba todos los engines disponibles** y selecciona el mejor resultado basándose en:
- Nivel de confianza del OCR
- Cantidad de texto extraído
- Score combinado

Si un engine falla, automáticamente usa los demás.

## 📊 Preprocesamiento Avanzado

- ✅ Conversión a escala de grises
- ✅ Redimensión 2x para mejorar OCR
- ✅ Reducción de ruido (denoising)
- ✅ Binarización adaptativa
- ✅ Corrección de inclinación (deskew)

## Detalles técnicos

### Sistema Multi-Engine OCR

El bot utiliza **3 engines de OCR** con sistema de fallback automático:

```python
engines = ['tesseract', 'easyocr', 'paddleocr']
```

**Proceso de selección:**
1. Ejecuta todos los engines disponibles en paralelo
2. Calcula score para cada resultado: `confidence × (0.7 + 0.3 × text_length_factor)`
3. Selecciona el engine con mejor score
4. Si todos fallan, retorna error

### Extracción con Confidence Scoring

Cada campo extraído incluye su nivel de confianza:

**Ejemplo de resultado:**
```python
{
    'amount': 29.86,
    'amount_confidence': 95,  # Alta confianza
    'date': '2026-01-07',
    'date_confidence': 90,
    'title': 'GRUPO DIA',
    'title_confidence': 85,
    'category': 'Comida',
    'category_confidence': 60,
    'overall_confidence': 82.5,  # Promedio ponderado
    'ocr_engine': 'tesseract'  # Engine que dio mejor resultado
}
```

### Extracción de montos

El extractor de montos utiliza patrones con prioridad para identificar correctamente el importe pagado:

**Prioridad alta (confianza 90-95%):**
- `IMPORTE TARJETA` - Monto pagado con tarjeta
- `IMPORTE PAGADO` - Importe total pagado
- `TOTAL A PAGAR` - Total a pagar

**Prioridad media (confianza 60-80%):**
- `TOTAL COMPRA` - Total de la compra
- `TOTAL` - Cualquier total
- `IMPORTE` - Cualquier importe

Los patrones permiten saltos de línea y caracteres entre el texto y el monto.

### Extracción de fechas

El extractor busca fechas en múltiples formatos con validación:

**Formatos soportados:**
- `AAAAMMDD` (códigos de ticket) - conf: 50-90%
- `DD/MM/AAAA` o `DD-MM-AAAA` - conf: 60-90%
- `AAAA/MM/DD` o `YYYY-MM-DD` - conf: 70-90%

**Validación:**
- Solo acepta años entre 2020 y 2030
- La fecha no puede ser futura
- Si no detecta fecha válida, marca `1900-01-01` con confianza 0%

### Extracción de títulos

Extrae el nombre del comercio de las primeras líneas del ticket:
- Primera línea: confianza 85%
- Segunda línea: confianza 70%
- Tercera línea: confianza 50%

Limpia números y espacios redundantes.

### Clasificación de categorías

Clasifica automáticamente usando **keywords**:

```python
category_keywords = {
    'Comida': ['supermerc', 'alimenta', 'restaur', 'dia', 'mercadona', ...],
    'Transporte': ['gasolina', 'taxi', 'parking', ...],
    'Compras': ['optic', 'ropa', 'tienda', ...],
    'Entretenimiento': ['cine', 'teatro', 'museo', ...],
    'Otros': []
}
```

La confianza depende del número de keywords encontradas.

## Requisitos previos

### 1. Instalar Tesseract OCR

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**MacOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Descargar desde https://github.com/UB-Mannheim/tesseract/wiki

### 2. Crear un bot de Telegram

1. Abre @BotFather en Telegram
2. Envía `/newbot`
3. Sigue las instrucciones para crear tu bot
4. Copia el token que te proporciona

## Instalación

### Opción 1: Docker (Recomendado)

1. Clona el repositorio y entra en el directorio:
```bash
cd expense-tracker-bot
```

2. Configura las variables de entorno:
```bash
cp .env.example .env
```

3. Edita el archivo `.env` y pega tu token:
```
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

4. Construye y ejecuta con Docker:

**Método A: Script automático** (recomendado)
```bash
./build.sh
# Selecciona opción 1 (LIGHT) - Tesseract + EasyOCR
```

**Método B: Manual**
```bash
docker compose build  # Construye imagen (~10-15 min)
docker compose up -d  # Inicia el bot
```

**Configuraciones disponibles:**
- **LIGHT** (default): Tesseract + EasyOCR - ~2GB, 10-15 min build
- **FULL**: Todos los engines - ~4GB, 20-30 min build (ver [OCR_ENGINES.md](OCR_ENGINES.md))
- **MINIMAL**: Solo Tesseract - ~100MB, 2-3 min build (no recomendado)

Para ver los logs en tiempo real:
```bash
docker logs -f expense-tracker-bot
```

Para detener el bot:
```bash
docker compose down
```

### Opción 2: Instalación local

**Nota:** Ver [OCR_ENGINES.md](OCR_ENGINES.md) para opciones de instalación (FULL/LIGHT/MINIMAL).

1. Instala Tesseract OCR (requerido):

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

**MacOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Descargar desde https://github.com/UB-Mannheim/tesseract/wiki

2. Clona el repositorio:
```bash
cd expense-tracker-bot
```

3. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

4. Instala las dependencias:

**Instalación LIGHT** (recomendado - Tesseract + EasyOCR):
```bash
pip install -r requirements-light.txt
```

**Instalación FULL** (todos los engines):
```bash
pip install -r requirements.txt
```

5. Configura las variables de entorno:
```bash
cp .env.example .env
# Edita .env con tu token
```

6. Ejecuta el bot:
```bash
python bot.py
```

## 📊 Ejemplo de Salida

Cuando envías una foto de un ticket, el bot responde con:

```
🏪 GRUPO DIA
💰 Monto: $29.86 (conf: 95%)
📅 Fecha: 2026-01-07 (conf: 90%)
📂 Categoría sugerida: Comida (conf: 60%)
🔧 Engine: tesseract
🟢 Confianza general: 82.5%

Selecciona o confirma la categoría:
⭐ Comida | Transporte | Compras | Entretenimiento | Otros
```

**Indicadores de confianza:**
- 🟢 **80-100%**: Datos muy confiables - usar sin revisión
- 🟡 **60-79%**: Revisar datos importantes (ej: monto)
- 🔴 **0-59%**: Verificar manualmente todos los datos

## Uso

**Con Docker:**
```bash
docker compose up -d
```

**Localmente:**
```bash
python bot.py
```

En Telegram, abre una conversación con tu bot y envíale `/start` para comenzar.

Sube una foto de un ticket y el bot analizará la imagen, extraerá:
- 💰 Monto pagado (con confianza %)
- 📅 Fecha del ticket (con confianza %)
- 🏪 Nombre del comercio (con confianza %)
- 📂 Categoría sugerida automáticamente (con confianza %)
- 🔧 Engine de OCR utilizado
- 🎯 Confianza general del análisis

El bot te mostrará la **categoría sugerida** (marcada con ⭐) basada en el contenido del ticket.
Puedes confirmarla o seleccionar otra categoría:
- Comida
- Transporte
- Compras
- Entretenimiento
- Otros

## Formato del CSV

El archivo `data/expenses.csv` tendrá el siguiente formato:

| date | amount | category | telegram_user | processed_at | receipt_path | title |
|------|--------|----------|---------------|--------------|--------------|-------|
| 2024-01-09 | 25.50 | Comida | username | 2024-01-09 15:30:00 | data/receipts/receipt_123.jpg | Tienda XYZ |
| 1900-01-01 | 154.00 | Compras | username | 2024-01-09 15:35:00 | data/receipts/receipt_456.jpg | OPTIGARBERY |

**Notas:**
- `date`: Fecha del ticket o `1900-01-01` si no se detectó
- `receipt_path`: Ruta a la imagen guardada
- `title`: Nombre del comercio extraído del ticket

## Tests automatizados

El proyecto incluye tests automatizados comprehensivos con validación de confianza:

### Tests básicos (legacy):
```bash
docker exec expense-tracker-bot python test_receipts.py
```

### Tests comprehensivos multi-engine:
```bash
docker exec expense-tracker-bot python test_receipts_v2.py
```

Los tests validan:
- ✅ Extracción correcta de montos con confianza
- ✅ Extracción de fechas con confianza
- ✅ Extracción de títulos con confianza
- ✅ Clasificación de categorías con confianza
- ✅ Confianza general del análisis
- ✅ Funcionamiento de cada engine de OCR
- ✅ Sistema de fallback entre engines
- ✅ Manejo de tickets sin fecha

**Salida esperada:**
```
================================================================================
COMPREHENSIVE OCR TESTS - ALL RECEIPTS
================================================================================

[TEST 1/5] receipt_20260109_155213.jpg
--------------------------------------------------------------------------------
  💰 Amount: €154.00 (confidence: 95%)
  📅 Date: 1900-01-01 (confidence: 0%)
  🏪 Title: SOLOPTICAL TORRE TRIANA (confidence: 85%)
  📂 Category: Compras (confidence: 60%)
  🎯 Overall Confidence: 72.0%
  🔧 OCR Engine: tesseract (89.5%)

  ✅ TEST PASSED

...

================================================================================
FINAL RESULT: 5/5 TESTS PASSED | 0/5 TESTS FAILED
================================================================================

Confidence Statistics:
  Average: 75.2%
  Minimum: 68.5%
  Maximum: 85.3%
```

### Comparación de engines:

```bash
docker exec expense-tracker-bot python test_receipts_v2.py
```

Compara el rendimiento de Tesseract vs EasyOCR vs PaddleOCR en el mismo ticket.

## Estructura del proyecto

```
expense-tracker-bot/
├── bot.py                      # Bot de Telegram con UI mejorada
├── receipt_analyzer.py         # Análisis legacy (Tesseract solo)
├── receipt_analyzer_v2.py      # 🆕 Análisis multi-engine con confidence
├── csv_handler.py              # Manejo del archivo CSV
├── test_receipts.py            # Tests legacy
├── test_receipts_v2.py         # 🆕 Tests comprehensivos multi-engine
├── requirements.txt            # Dependencias (Tesseract, EasyOCR, PaddleOCR)
├── Dockerfile                  # Configuración Docker con todos los engines
├── docker-compose.yml          # Configuración de Docker Compose
├── .env.example                # Ejemplo de configuración
├── data/                       # Directorio de datos (volumen Docker)
│   ├── expenses.csv           # Archivo CSV con gastos
│   └── receipts/             # Imágenes de tickets
└── README.md                  # Este archivo
```

## Depuración

Para ver logs detallados del análisis:

```bash
docker logs -f expense-tracker-bot | grep DEBUG
```

Los logs muestran:
- Texto extraído por el OCR
- Patrones encontrados para montos y fechas
- Montos y fechas detectadas
- Errores de procesamiento

### Problemas comunes

**El bot no detecta fechas:**
- Verifica que el ticket tenga una fecha visible
- El OCR solo detecta fechas en el rango 2020-2030
- Si no hay fecha, el bot muestra: `❌ No se pudo detectar la fecha` (confianza 0%)

**El bot detecta el monto incorrecto:**
- Revisa la imagen del ticket en `data/receipts/`
- Los patrones priorizan "IMPORTE TARJETA" sobre montos de IVA
- Envía una foto más clara o con mejor iluminación
- Verifica el nivel de confianza: <60% indica que debes revisar manualmente

**El bot no procesa fotos:**
- Verifica que el contenedor esté corriendo: `docker ps`
- Revisa los logs para errores: `docker logs expense-tracker-bot`
- Asegúrate de que el token sea correcto en `.env`

**Baja confianza en el análisis (<60%):**
- Toma una foto más clara con buena iluminación
- Asegúrate de que el ticket esté plano (sin arrugas)
- El ticket debe estar bien enfocado
- Evita sombras o brillos excesivos

**Error al inicializar engines de OCR:**
- Reconstruye el contenedor: `docker compose up --build -d`
- Verifica espacio en disco: `df -h`
- Revisa logs del contenedor durante el inicio

## Mejoras futuras

- [ ] Soporte para más idiomas de OCR
- [ ] API REST para integración con otras apps
- [ ] Fine-tuning de modelos de OCR con tickets específicos
- [ ] Detección automática de moneda (EUR, USD, etc)
- [ ] Base de datos (SQLite/PostgreSQL)
- [ ] Dashboard web para visualizar gastos
- [ ] Estadísticas y gráficos con confianza agregada
- [ ] Exportación a Excel con scores de confianza
- [ ] Múltiples usuarios con autenticación
- [ ] Edición de gastos registrados
- [ ] Categorías personalizables
- [ ] Reportes mensuales/anuales
- [ ] Machine Learning para mejorar extracción
- [ ] Detección de duplicados
