from typing import Dict, Optional

from app.storage.csv_store import CSVStore
from app.storage.pg_store import PostgresStore


class ExpenseStore:
    def __init__(self, csv_store: CSVStore, pg_store: Optional[PostgresStore]) -> None:
        self.csv_store = csv_store
        self.pg_store = pg_store

    def save_expense(self, expense: Dict[str, object]) -> None:
        if self.pg_store:
            self.pg_store.save_expense(expense)
        self.csv_store.save_expense(expense)
