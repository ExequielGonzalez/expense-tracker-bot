# Expense Tracker Bot

Bot de Telegram que registra gastos desde tickets usando **qwen3-vl** y permite cargar gastos manuales.

## 🚀 Características

- 📷 Analiza fotos de tickets con modelo de visión (qwen3-vl)
- 🧾 Registro manual con `/gasto` (flujo guiado)
- 💳 Pregunta quién pagó (Exe/Ceci por defecto)
- 💾 Guarda en Postgres y CSV
- 🖼️ Guarda las imágenes en `data/receipts`
- ✅ Tests de integración para V3 (Ollama)
- 🧩 Arquitectura modular (handlers + storage)

## Requisitos previos

### 1. Crear un bot de Telegram

1. Abre @BotFather en Telegram
2. Envía `/newbot`
3. Sigue las instrucciones para crear tu bot
4. Copia el token que te proporciona

### 2. Ollama con modelo qwen3-vl

Asegúrate de tener Ollama corriendo y el modelo descargado:

```bash
ollama pull qwen3-vl:4b-instruct
```

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

3. Edita `.env` con tu token y configuración de DB. Ejemplo:
```
TELEGRAM_BOT_TOKEN=tu_token
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3-vl:4b-instruct
PAYERS=Exe,Ceci
POSTGRES_USER=expenses
POSTGRES_PASSWORD=expenses
POSTGRES_DB=expenses
DATABASE_URL=postgresql://expenses:expenses@localhost:5432/expenses
```

4. Construye y ejecuta:
```bash
./build.sh
docker compose up -d
```

5. Si lo usas en grupos, desactiva Privacy Mode en BotFather para que el bot reciba fotos.

Para ver logs:
```bash
docker logs -f expense-tracker-bot
```

Para detener:
```bash
docker compose down
```

### Opción 2: Instalación local

1. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Configura variables:
```bash
cp .env.example .env
```

4. Ejecuta el bot:
```bash
python bot.py
```

## Uso

- Envía `/start` para ver la ayuda.
- Envía una foto de ticket para analizar.
- Usa `/gasto` para cargar un gasto manual.

## Formato del CSV

El archivo `data/expenses.csv` incluye:

| date | amount | category | payer | telegram_user | chat_id | message_id | processed_at | source | receipt_path | receipt_file_id | title | model | overall_confidence |
|------|--------|----------|-------|---------------|---------|------------|--------------|--------|--------------|-----------------|-------|-------|--------------------|

## Tests

```bash
python test_receipts_v3.py --quick
```

## Comandos del bot

El bot configura automáticamente:
- `/start`
- `/gasto`

## Estructura del proyecto

```
expense-tracker-bot/
├── app/
│   ├── handlers/
│   ├── storage/
│   ├── boot.py
│   ├── config.py
│   └── telegram_app.py
├── bot.py
├── receipt_analyzer_v3.py
├── docker-compose.yml
└── data/
```

## Notas sobre grupos

Para que el bot reciba fotos en grupos, desactiva **Privacy Mode** en BotFather.

## Base de datos

La tabla `expenses` se crea automáticamente al iniciar. Campos clave:
- `payer` (Exe/Ceci)
- `source` (`photo` o `manual`)
- `receipt_path` y `receipt_file_id`