import csv
import os
from typing import Dict, List


class CSVStore:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.headers = [
            'date',
            'amount',
            'category',
            'payer',
            'telegram_user',
            'chat_id',
            'message_id',
            'processed_at',
            'source',
            'receipt_path',
            'receipt_file_id',
            'title',
            'model',
            'overall_confidence'
        ]
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()

    def save_expense(self, expense: Dict[str, object]) -> None:
        with open(self.filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writerow(expense)

    def get_all_expenses(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.filename):
            return []

        with open(self.filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
