from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.config import CATEGORIES, PAYERS
from app.handlers.common import build_expense_payload, parse_date_input
from app.storage.store import ExpenseStore

STEP_AMOUNT = 1
STEP_DATE = 2
STEP_TITLE = 3
STEP_CATEGORY = 4
STEP_PAYER = 5
STEP_CONFIRM = 6


async def start_manual_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['manual_expense'] = {}
    await update.message.reply_text(
        '🧾 Registro manual de gasto\n\nIngresa el monto (ej: 12.50)'
    )
    return STEP_AMOUNT


async def manual_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(',', '.')
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text('❌ Monto inválido. Usa formato 12.50')
        return STEP_AMOUNT

    if amount <= 0 or amount > 100000:
        await update.message.reply_text('❌ Monto inválido. Usa un valor entre 0 y 100000')
        return STEP_AMOUNT

    context.user_data['manual_expense']['amount'] = round(amount, 2)
    await update.message.reply_text(
        "📅 Fecha del gasto (YYYY-MM-DD). Escribe 'hoy' para usar la fecha actual."
    )
    return STEP_DATE


async def manual_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text or text.lower() == 'hoy':
        date_value = datetime.now().strftime('%Y-%m-%d')
    else:
        date_value = parse_date_input(text)
        if not date_value:
            await update.message.reply_text('❌ Fecha inválida. Usa YYYY-MM-DD (no futura).')
            return STEP_DATE

    context.user_data['manual_expense']['date'] = date_value

    await update.message.reply_text('🏷️ Título del gasto (ej: Supermercado)')
    return STEP_TITLE


async def manual_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text('❌ El título no puede estar vacío.')
        return STEP_TITLE

    context.user_data['manual_expense']['title'] = title

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"manual_category|{cat}") for cat in CATEGORIES[:3]],
        [InlineKeyboardButton(cat, callback_data=f"manual_category|{cat}") for cat in CATEGORIES[3:]]
    ]
    await update.message.reply_text(
        '📂 Selecciona la categoría:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP_CATEGORY


async def manual_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split('|', 1)
    if len(data) != 2 or data[0] != 'manual_category':
        await query.edit_message_text('❌ Categoría inválida.')
        return ConversationHandler.END

    category = data[1]
    if category not in CATEGORIES:
        await query.edit_message_text('❌ Categoría inválida.')
        return ConversationHandler.END

    context.user_data['manual_expense']['category'] = category

    keyboard = [[InlineKeyboardButton(payer, callback_data=f"manual_payer|{payer}") for payer in PAYERS]]
    await query.edit_message_text(
        '💳 ¿Quién pagó?',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STEP_PAYER


async def manual_payer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split('|', 1)
    if len(data) != 2 or data[0] != 'manual_payer':
        await query.edit_message_text('❌ Pagador inválido.')
        return ConversationHandler.END

    payer = data[1]
    if payer not in PAYERS:
        await query.edit_message_text('❌ Pagador inválido.')
        return ConversationHandler.END

    context.user_data['manual_expense']['payer'] = payer

    data = context.user_data['manual_expense']
    summary = (
        f"✅ Resumen del gasto\n"
        f"• Título: {data['title']}\n"
        f"• Monto: ${data['amount']:.2f}\n"
        f"• Fecha: {data['date']}\n"
        f"• Categoría: {data['category']}\n"
        f"• Pagó: {data['payer']}\n\n"
        "¿Confirmar?"
    )

    keyboard = [[
        InlineKeyboardButton('Guardar', callback_data='manual_confirm|confirm'),
        InlineKeyboardButton('Cancelar', callback_data='manual_confirm|cancel')
    ]]

    await query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_CONFIRM


async def manual_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data.split('|', 1)
    if len(data) != 2 or data[0] != 'manual_confirm':
        await query.edit_message_text('❌ Acción inválida.')
        return ConversationHandler.END

    if data[1] == 'cancel':
        await query.edit_message_text('❌ Gasto cancelado.')
        return ConversationHandler.END

    data = context.user_data.get('manual_expense', {})
    if not data:
        await query.edit_message_text('❌ No hay datos para guardar.')
        return ConversationHandler.END

    store: ExpenseStore = context.application.bot_data['store']

    processed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    payload = build_expense_payload(
        date=data['date'],
        amount=data['amount'],
        category=data['category'],
        payer=data['payer'],
        telegram_user=update.effective_user.username or 'unknown',
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id,
        processed_at=processed_at,
        source='manual',
        receipt_path=None,
        receipt_file_id=None,
        title=data['title'],
        model=None,
        overall_confidence=None
    )

    store.save_expense(payload)
    context.user_data.pop('manual_expense', None)

    await query.edit_message_text(
        f"✅ Gasto guardado\n"
        f"• Título: {data['title']}\n"
        f"• Monto: ${data['amount']:.2f}\n"
        f"• Fecha: {data['date']}\n"
        f"• Categoría: {data['category']}\n"
        f"• Pagó: {data['payer']}"
    )
    return ConversationHandler.END


async def manual_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop('manual_expense', None)
    await update.message.reply_text('❌ Registro manual cancelado.')
    return ConversationHandler.END
