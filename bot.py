import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# It's better to use a free API like Fixer.io or Open Exchange Rates.
# Note: Free tiers often have a base currency (like EUR) and limited calls.
API_KEY = os.getenv('EXCHANGE_API_KEY') # Optional but recommended
BASE_URL = "http://api.exchangerate-api.com/v4/latest/"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
async def get_exchange_rate(base_currency, target_currency):
    """Fetches the exchange rate from a free API."""
    try:
        # Using exchangerate-api.com as a free example
        response = requests.get(f"{BASE_URL}{base_currency.upper()}")
        response.raise_for_status()
        data = response.json()
        rate = data['rates'].get(target_currency.upper())
        if rate is None:
            return None, f"Currency '{target_currency}' not supported."
        return rate, None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None, "Failed to fetch exchange rates. Please try again later."

# --- Bot Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and keyboard."""
    keyboard = [
        [InlineKeyboardButton("Convert Currency", callback_data='convert')],
        [InlineKeyboardButton("Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Hello! I'm a currency converter bot.\n"
        "You can send me a message like '100 USD to EUR' or use the buttons below.",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message."""
    help_text = (
        "Here are the ways you can use me:\n"
        "1. Send a direct message: `100 USD to EUR`\n"
        "2. Send a command: `/convert 100 USD EUR`\n"
        "3. Use the interactive buttons.\n\n"
        "Supported currencies are from exchangerate-api.com (e.g., USD, EUR, GBP, JPY, BTC, etc.)."
    )
    await update.message.reply_text(help_text)

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /convert command."""
    try:
        # Expects format: /convert 100 USD EUR
        amount = float(context.args[0])
        base_currency = context.args[1].upper()
        target_currency = context.args[2].upper()
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /convert <amount> <from_currency> <to_currency>\nExample: /convert 100 USD EUR")
        return

    rate, error = await get_exchange_rate(base_currency, target_currency)
    if error:
        await update.message.reply_text(error)
        return

    converted_amount = amount * rate
    await update.message.reply_text(f"💰 {amount} {base_currency} = {converted_amount:.2f} {target_currency} (Rate: 1 {base_currency} = {rate:.4f} {target_currency})")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages that look like currency conversions."""
    text = update.message.text
    # Simple parser for messages like "100 USD to EUR" or "50 GBP in JPY"
    parts = text.split()
    if len(parts) == 4 and parts[2].lower() in ['to', 'in']:
        try:
            amount = float(parts[0])
            base_currency = parts[1].upper()
            target_currency = parts[3].upper()
        except ValueError:
            await update.message.reply_text("Invalid format. Try: `100 USD to EUR`")
            return

        rate, error = await get_exchange_rate(base_currency, target_currency)
        if error:
            await update.message.reply_text(error)
            return

        converted_amount = amount * rate
        await update.message.reply_text(f"💰 {amount} {base_currency} = {converted_amount:.2f} {target_currency}")
    else:
        await update.message.reply_text("I'm not sure what you mean. Try sending '100 USD to EUR' or type /help.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == 'convert':
        await query.edit_message_text("To convert, send me a message like:\n`100 USD to EUR`\nor use the command:\n`/convert 100 USD EUR`")
    elif query.data == 'help':
        help_text = (
            "Here are the ways you can use me:\n"
            "1. Send a direct message: `100 USD to EUR`\n"
            "2. Send a command: `/convert 100 USD EUR`\n"
            "3. Use the interactive buttons.\n\n"
            "Supported currencies are from exchangerate-api.com (e.g., USD, EUR, GBP, JPY, BTC, etc.)."
        )
        await query.edit_message_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs errors caused by updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    """Starts the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("convert", convert))

    # Register message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot (Long Polling)
    logger.info("Starting bot with long polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
