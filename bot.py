import os
import re
import csv
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from csv_handler import CSVHandler

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ANALYZER_VERSION = os.getenv('ANALYZER_VERSION', 'v2').lower()
DATA_DIR = 'data'
CSV_FILE = os.path.join(DATA_DIR, 'expenses.csv')
RECEIPTS_DIR = os.path.join(DATA_DIR, 'receipts')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RECEIPTS_DIR, exist_ok=True)

# Initialize analyzer based on ANALYZER_VERSION env var
# Options: v2 (OCR multi-engine), v3 (Ollama Vision LLM)
if ANALYZER_VERSION == 'v3':
    try:
        from receipt_analyzer_v3 import ReceiptAnalyzerV3
        receipt_analyzer = ReceiptAnalyzerV3()
        print("[INFO] Using ReceiptAnalyzerV3 (Ollama Vision LLM)")
    except Exception as e:
        print(f"[WARN] Could not initialize V3 analyzer: {e}")
        print("[INFO] Falling back to V2 (OCR multi-engine)")
        from receipt_analyzer_v2 import ReceiptAnalyzerV2
        receipt_analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr', 'paddleocr'])
else:
    # Default: V2 multi-engine OCR
    from receipt_analyzer_v2 import ReceiptAnalyzerV2
    try:
        receipt_analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr', 'paddleocr'])
        print("[INFO] Using ReceiptAnalyzerV2 - OCR engines: Tesseract, EasyOCR, PaddleOCR")
    except Exception as e:
        print(f"[WARN] Could not initialize all OCR engines: {e}")
        print("[INFO] Falling back to Tesseract + EasyOCR")
        receipt_analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr'])

csv_handler = CSVHandler(CSV_FILE)

pending_receipts = {}
pending_manual_input = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '¡Hola! 👋 Soy tu bot de análisis de gastos con OCR multi-engine.\n\n'
        'Sube una foto de tu ticket y extraeré:\n'
        '• 💰 Monto pagado\n'
        '• 📅 Fecha del ticket\n'
        '• 🏪 Nombre del comercio\n'
        '• 📂 Categoría sugerida\n'
        '• 🎯 Nivel de confianza del análisis\n\n'
        'Uso 3 engines de OCR (Tesseract, EasyOCR, PaddleOCR) con fallback automático.\n'
        'Los datos se guardarán en un archivo CSV.'
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    receipt_path = os.path.join(RECEIPTS_DIR, f'receipt_{timestamp}.jpg')
    receipt_id = f'{update.message.message_id}_{timestamp}'
    
    await file.download_to_drive(receipt_path)
    print(f"[DEBUG] Foto guardada en: {receipt_path}")
    
    await update.message.reply_text('🔍 Analizando el ticket con 3 engines OCR...')
    
    try:
        receipt_data = receipt_analyzer.analyze_receipt(receipt_path)
        
        print(f"[DEBUG] Resultado del análisis: {receipt_data}")
        
        if receipt_data:
            date_display = receipt_data['date']
            if receipt_data['date'] == '1900-01-01':
                date_display = '❌ No se pudo detectar la fecha'
            
            # Get confidence icon
            conf = receipt_data['overall_confidence']
            if conf >= 80:
                conf_icon = '🟢'
            elif conf >= 60:
                conf_icon = '🟡'
            else:
                conf_icon = '🔴'
            
            pending_receipts[receipt_id] = {
                'amount': receipt_data['amount'],
                'date': receipt_data['date'],
                'receipt_path': receipt_path,
                'title': receipt_data.get('title', 'Sin título'),
                'suggested_category': receipt_data.get('category', 'Otros'),
                'confidence': receipt_data['overall_confidence']
            }
            
            # Put suggested category first
            suggested = receipt_data.get('category', 'Otros')
            categories = ['Comida', 'Transporte', 'Compras', 'Entretenimiento', 'Otros']
            if suggested in categories:
                categories.remove(suggested)
                categories.insert(0, suggested)
            
            keyboard = [
                [InlineKeyboardButton(
                    f"{'⭐ ' if cat == suggested else ''}{cat}", 
                    callback_data=f'{receipt_id}|{cat}'
                ) for cat in categories[:3]],
                [InlineKeyboardButton(cat, callback_data=f'{receipt_id}|{cat}') for cat in categories[3:]]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f'🏪 {receipt_data.get("title", "Sin título")}\n'
                f'💰 Monto: ${receipt_data["amount"]} (conf: {receipt_data["amount_confidence"]}%)\n'
                f'📅 Fecha: {date_display} (conf: {receipt_data["date_confidence"]}%)\n'
                f'📂 Categoría sugerida: {receipt_data.get("category", "Otros")} (conf: {receipt_data["category_confidence"]}%)\n'
                f'🔧 Engine: {receipt_data["ocr_engine"]}\n'
                f'{conf_icon} Confianza general: {receipt_data["overall_confidence"]}%\n\n'
                'Selecciona o confirma la categoría:',
                reply_markup=reply_markup
            )
        else:
            # OCR failed - ask user for manual input
            pending_manual_input[receipt_id] = {
                'receipt_path': receipt_path,
                'user_id': update.effective_user.id,
                'chat_id': update.effective_chat.id
            }
            
            await update.message.reply_text(
                '❌ No pude extraer el monto del ticket con ninguno de los 3 engines OCR.\n\n'
                '💡 Por favor, ingresa el monto manualmente en formato: 123.45\n'
                '(Usa punto decimal, ejemplo: 154.00 o 3.50)'
            )
    except Exception as e:
        print(f"[DEBUG] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f'❌ Error al procesar: {str(e)}')

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    receipt_id, category = query.data.split('|')
    
    receipt_info = pending_receipts.get(receipt_id)
    
    if not receipt_info:
        await query.edit_message_text('❌ Error: Información del ticket no encontrada')
        return
    
    expense = {
        'date': receipt_info['date'],
        'amount': receipt_info['amount'],
        'category': category,
        'telegram_user': update.effective_user.username or 'unknown',
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'receipt_path': receipt_info['receipt_path'],
        'title': receipt_info.get('title', 'Sin título')
    }
    
    csv_handler.save_expense(expense)
    del pending_receipts[receipt_id]
    
    await query.edit_message_text(
        f'✅ Gasto guardado!\n'
        f'• {receipt_info.get("title", "Sin título")}\n'
        f'• Monto: ${receipt_info["amount"]}\n'
        f'• Categoría: {category}\n'
        f'• Fecha: {receipt_info["date"]}'
    )

async def handle_manual_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle manual amount input when OCR fails"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Find pending manual input for this user
    receipt_id = None
    for rid, info in pending_manual_input.items():
        if info['user_id'] == user_id:
            receipt_id = rid
            break
    
    if not receipt_id:
        # No pending manual input, ignore this message
        return
    
    # Parse amount
    try:
        # Accept formats: 123.45, 123,45, 123
        amount_str = text.replace(',', '.')
        amount = float(amount_str)
        
        if amount <= 0 or amount > 100000:
            await update.message.reply_text(
                '❌ Monto inválido. Por favor ingresa un valor entre 0 y 100,000.\n'
                'Ejemplo: 154.00 o 3.50'
            )
            return
        
        # Store receipt data with manual amount
        receipt_info = pending_manual_input[receipt_id]
        today = datetime.now().strftime('%Y-%m-%d')
        
        pending_receipts[receipt_id] = {
            'amount': amount,
            'date': today,
            'receipt_path': receipt_info['receipt_path'],
            'title': 'Manual',
            'suggested_category': 'Otros',
            'confidence': 0
        }
        
        del pending_manual_input[receipt_id]
        
        # Ask for category
        categories = ['Comida', 'Transporte', 'Compras', 'Entretenimiento', 'Otros']
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f'{receipt_id}|{cat}') for cat in categories[:3]],
            [InlineKeyboardButton(cat, callback_data=f'{receipt_id}|{cat}') for cat in categories[3:]]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f'✅ Monto recibido: ${amount:.2f}\n'
            f'📅 Fecha: {today} (hoy)\n\n'
            'Selecciona la categoría:',
            reply_markup=reply_markup
        )
        
    except ValueError:
        await update.message.reply_text(
            '❌ Formato inválido. Por favor ingresa solo el número.\n'
            'Ejemplo: 154.00 o 3.50'
        )

def main():
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN no está configurado")
        return
    
    print("[INFO] Iniciando bot de gastos...")
    print(f"[INFO] Token configurado: {TOKEN[:20]}...")
    print(f"[INFO] Directorio de datos: {DATA_DIR}")
    print(f"[INFO] Archivo CSV: {CSV_FILE}")
    print(f"[INFO] Directorio de receipts: {RECEIPTS_DIR}")
    
    app = Application.builder().token(TOKEN).build()
    
    print("[INFO] Registrando handlers...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_amount))
    app.add_handler(CallbackQueryHandler(category_selected))
    
    print("[INFO] Iniciando polling...")
    print("[INFO] Bot listo para recibir mensajes.")
    app.run_polling()

if __name__ == '__main__':
    main()
