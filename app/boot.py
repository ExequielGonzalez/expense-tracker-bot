from app.config import CSV_FILE, DATABASE_URL
from app.storage.csv_store import CSVStore
from app.storage.pg_store import build_postgres_store
from app.storage.store import ExpenseStore
from receipt_analyzer_v3 import ReceiptAnalyzerV3


def build_dependencies():
    csv_store = CSVStore(CSV_FILE)
    try:
        pg_store = build_postgres_store(DATABASE_URL)
    except Exception as exc:
        print(f"[WARN] Postgres no disponible: {exc}")
        pg_store = None

    analyzer = ReceiptAnalyzerV3()
    store = ExpenseStore(csv_store, pg_store)
    pending_receipts = {}

    return {
        'store': store,
        'analyzer': analyzer,
        'pending_receipts': pending_receipts
    }
