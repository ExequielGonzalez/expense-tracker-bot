import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.getenv('DATA_DIR', 'data')
CSV_FILE = os.getenv('CSV_FILE', os.path.join(DATA_DIR, 'expenses.csv'))
RECEIPTS_DIR = os.getenv('RECEIPTS_DIR', os.path.join(DATA_DIR, 'receipts'))

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

CATEGORIES = ['Comida', 'Transporte', 'Compras', 'Entretenimiento', 'Otros']

PAYERS = [payer.strip() for payer in os.getenv('PAYERS', 'Exe,Ceci').split(',') if payer.strip()]

BOT_COMMANDS = [
    ('start', 'Ver ayuda'),
    ('gasto', 'Registrar gasto manual')
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RECEIPTS_DIR, exist_ok=True)
