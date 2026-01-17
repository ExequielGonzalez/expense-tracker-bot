from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from app.config import BOT_COMMANDS, TELEGRAM_BOT_TOKEN
from app.handlers.manual import (
    STEP_AMOUNT,
    STEP_CATEGORY,
    STEP_CONFIRM,
    STEP_DATE,
    STEP_PAYER,
    STEP_TITLE,
    manual_amount,
    manual_cancel,
    manual_category,
    manual_confirm,
    manual_date,
    manual_payer,
    manual_title,
    start_manual_expense
)
from app.handlers.photo import handle_photo, category_selected, payer_selected
from app.handlers.start import start


async def set_bot_commands(app: Application) -> None:
    commands = [BotCommand(command, description) for command, description in BOT_COMMANDS]
    await app.bot.set_my_commands(commands)


def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError('TELEGRAM_BOT_TOKEN no está configurado')

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(set_bot_commands).build()

    app.add_handler(CommandHandler('start', start))

    manual_handler = ConversationHandler(
        entry_points=[CommandHandler('gasto', start_manual_expense)],
        states={
            STEP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_amount)],
            STEP_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_date)],
            STEP_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, manual_title)],
            STEP_CATEGORY: [CallbackQueryHandler(manual_category, pattern=r'^manual_category\|')],
            STEP_PAYER: [CallbackQueryHandler(manual_payer, pattern=r'^manual_payer\|')],
            STEP_CONFIRM: [CallbackQueryHandler(manual_confirm, pattern=r'^manual_confirm\|')]
        },
        fallbacks=[CommandHandler('cancel', manual_cancel)],
        per_chat=True,
        per_user=True
    )
    app.add_handler(manual_handler)

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(category_selected, pattern=r'^category\|'))
    app.add_handler(CallbackQueryHandler(payer_selected, pattern=r'^payer\|'))

    return app
