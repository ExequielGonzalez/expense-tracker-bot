from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '¡Hola! 👋 Soy tu bot de gastos con visión LLM.\n\n'
        'Puedes: \n'
        '• 📷 Enviar una foto de ticket\n'
        '• 🧾 Usar /gasto para registrar un gasto manual\n\n'
        'Los datos se guardan en CSV y Postgres.'
    )
