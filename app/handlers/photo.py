from datetime import datetime
from typing import Dict

from telegram import Update
from telegram.ext import ContextTypes

from app.config import RECEIPTS_DIR
from app.handlers.common import (
    PendingReceipt,
    build_category_keyboard,
    build_payer_keyboard,
    build_expense_payload
)
from app.storage.store import ExpenseStore
from receipt_analyzer_v3 import ReceiptAnalyzerV3


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]
    file = await photo.get_file()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    receipt_path = f"{RECEIPTS_DIR}/receipt_{timestamp}.jpg"

    await file.download_to_drive(receipt_path)

    await update.message.reply_text('🔍 Analizando el ticket con qwen3-vl...')

    analyzer: ReceiptAnalyzerV3 = context.application.bot_data['analyzer']

    try:
        receipt_data = analyzer.analyze_receipt(receipt_path)
    except Exception as exc:
        print(f"[WARN] Error al procesar ticket: {exc}")
        await update.message.reply_text('❌ Error al procesar el ticket.')
        return

    if not receipt_data:
        await update.message.reply_text('❌ No pude extraer datos del ticket. Prueba otra foto.')
        return

    date_display = receipt_data['date']
    if receipt_data['date'] == '1900-01-01':
        date_display = '❌ No se pudo detectar la fecha'

    conf = receipt_data['overall_confidence']
    if conf >= 80:
        conf_icon = '🟢'
    elif conf >= 60:
        conf_icon = '🟡'
    else:
        conf_icon = '🔴'

    pending = PendingReceipt(
        amount=receipt_data['amount'],
        date=receipt_data['date'],
        receipt_path=receipt_path,
        receipt_file_id=file.file_id,
        title=receipt_data.get('title', 'Sin título'),
        suggested_category=receipt_data.get('category', 'Otros'),
        confidence=receipt_data['overall_confidence'],
        model=receipt_data.get('model'),
        chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        telegram_user=update.effective_user.username or 'unknown'
    )

    pending_receipts: Dict[str, PendingReceipt] = context.application.bot_data['pending_receipts']
    receipt_id = f"{update.message.message_id}_{timestamp}"
    reply_markup = build_category_keyboard(pending.suggested_category)

    sent = await update.message.reply_text(
        f"🏪 {pending.title}\n"
        f"💰 Monto: ${pending.amount} (conf: {receipt_data['amount_confidence']}%)\n"
        f"📅 Fecha: {date_display} (conf: {receipt_data['date_confidence']}%)\n"
        f"📂 Categoría sugerida: {pending.suggested_category} (conf: {receipt_data['category_confidence']}%)\n"
        f"🔧 Modelo: {receipt_data['ocr_engine']}\n"
        f"{conf_icon} Confianza general: {pending.confidence}%\n\n"
        "Selecciona o confirma la categoría:",
        reply_markup=reply_markup
    )
    pending_receipts[receipt_id] = PendingReceipt(
        amount=pending.amount,
        date=pending.date,
        receipt_path=pending.receipt_path,
        receipt_file_id=pending.receipt_file_id,
        title=pending.title,
        suggested_category=pending.suggested_category,
        confidence=pending.confidence,
        model=pending.model,
        chat_id=pending.chat_id,
        message_id=pending.message_id,
        telegram_user=pending.telegram_user,
        prompt_message_id=sent.message_id
    )



async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('|', 1)
    if len(data) != 2 or data[0] != 'category':
        await query.edit_message_text('❌ Acción inválida.')
        return

    category = data[1]

    pending_receipts: Dict[str, PendingReceipt] = context.application.bot_data['pending_receipts']
    receipt_id = _find_pending_id(pending_receipts, query.message.message_id)

    if not receipt_id:
        await query.edit_message_text('❌ Error: Información del ticket no encontrada')
        return

    pending_receipts[receipt_id] = _replace_pending_category(pending_receipts[receipt_id], category)

    await query.edit_message_text(
        '💳 ¿Quién pagó?',
        reply_markup=build_payer_keyboard()
    )


async def payer_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('|', 1)
    if len(data) != 2 or data[0] != 'payer':
        await query.edit_message_text('❌ Acción inválida.')
        return

    payer = data[1]

    pending_receipts: Dict[str, PendingReceipt] = context.application.bot_data['pending_receipts']
    receipt_id = _find_pending_id(pending_receipts, query.message.message_id)

    if not receipt_id:
        await query.edit_message_text('❌ Error: Información del ticket no encontrada')
        return

    pending = pending_receipts[receipt_id]
    processed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    payload = build_expense_payload(
        date=pending.date,
        amount=pending.amount,
        category=pending.suggested_category,
        payer=payer,
        telegram_user=pending.telegram_user,
        chat_id=pending.chat_id,
        message_id=pending.message_id,
        processed_at=processed_at,
        source='photo',
        receipt_path=pending.receipt_path,
        receipt_file_id=pending.receipt_file_id,
        title=pending.title,
        model=pending.model,
        overall_confidence=pending.confidence
    )

    store: ExpenseStore = context.application.bot_data['store']
    store.save_expense(payload)

    pending_receipts.pop(receipt_id, None)

    await query.edit_message_text(
        f"✅ Gasto guardado!\n"
        f"• {pending.title}\n"
        f"• Monto: ${pending.amount}\n"
        f"• Categoría: {pending.suggested_category}\n"
        f"• Fecha: {pending.date}\n"
        f"• Pagó: {payer}"
    )


def _find_pending_id(pending_receipts: Dict[str, PendingReceipt], message_id: int):
    for receipt_id, receipt in pending_receipts.items():
        if receipt.prompt_message_id == message_id:
            return receipt_id
    return None


def _replace_pending_category(receipt: PendingReceipt, category: str) -> PendingReceipt:
    return PendingReceipt(
        amount=receipt.amount,
        date=receipt.date,
        receipt_path=receipt.receipt_path,
        receipt_file_id=receipt.receipt_file_id,
        title=receipt.title,
        suggested_category=category,
        confidence=receipt.confidence,
        model=receipt.model,
        chat_id=receipt.chat_id,
        message_id=receipt.message_id,
        telegram_user=receipt.telegram_user,
        prompt_message_id=receipt.prompt_message_id
    )
