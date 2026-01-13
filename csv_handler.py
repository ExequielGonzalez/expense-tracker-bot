import csv
import os
from datetime import datetime

class CSVHandler:
    def __init__(self, filename):
        self.filename = filename
        self.headers = ['date', 'amount', 'category', 'telegram_user', 'processed_at', 'receipt_path', 'title']
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
    
    def save_expense(self, expense):
        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(expense)
    
    def get_all_expenses(self):
        expenses = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                expenses = list(reader)
        return expenses
