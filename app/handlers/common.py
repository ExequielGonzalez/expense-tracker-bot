from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import CATEGORIES, PAYERS


@dataclass
class PendingReceipt:
    amount: float
    date: str
    receipt_path: Optional[str]
    receipt_file_id: Optional[str]
    title: str
    suggested_category: str
    confidence: float
    model: Optional[str]
    chat_id: int
    message_id: int
    telegram_user: str
    prompt_message_id: Optional[int] = None


def build_category_keyboard(suggested: str) -> InlineKeyboardMarkup:
    categories = list(CATEGORIES)
    if suggested in categories:
        categories.remove(suggested)
        categories.insert(0, suggested)

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'⭐ ' if cat == suggested else ''}{cat}",
                callback_data=f"category|{cat}"
            )
            for cat in categories[:3]
        ],
        [InlineKeyboardButton(cat, callback_data=f"category|{cat}") for cat in categories[3:]]
    ]

    return InlineKeyboardMarkup(keyboard)


def build_payer_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(payer, callback_data=f"payer|{payer}") for payer in PAYERS]]
    return InlineKeyboardMarkup(keyboard)


def parse_date_input(text: str) -> Optional[str]:
    clean = text.strip()
    if not clean:
        return None

    try:
        parsed = datetime.strptime(clean, '%Y-%m-%d')
    except ValueError:
        return None

    if parsed.date() > datetime.now().date():
        return None

    return parsed.strftime('%Y-%m-%d')


def build_expense_payload(
    *,
    date: str,
    amount: float,
    category: str,
    payer: str,
    telegram_user: str,
    chat_id: int,
    message_id: int,
    processed_at: str,
    source: str,
    receipt_path: Optional[str],
    receipt_file_id: Optional[str],
    title: Optional[str],
    model: Optional[str],
    overall_confidence: Optional[float]
) -> Dict[str, object]:
    return {
        'date': date,
        'amount': amount,
        'category': category,
        'payer': payer,
        'telegram_user': telegram_user,
        'chat_id': chat_id,
        'message_id': message_id,
        'processed_at': processed_at,
        'source': source,
        'receipt_path': receipt_path,
        'receipt_file_id': receipt_file_id,
        'title': title or 'Sin título',
        'model': model,
        'overall_confidence': overall_confidence
    }
