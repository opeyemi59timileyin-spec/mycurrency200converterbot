import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Currency API
BASE_URL = "http://api.exchangerate-api.com/v4/latest/"

def get_exchange_rate(base_currency, target_currency):
    """Fetches exchange rate from free API."""
    try:
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

# Command Handlers
def start(update, context):
    """Send welcome message with inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("💱 Convert Currency", callback_data='convert')],
        [InlineKeyboardButton("❓ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "👋 Welcome to My Currency Converter!\n\n"
        "I can convert between 150+ currencies.\n"
        "Just send me a message like:\n"
        "`100 USD to EUR`\n"
        "or use the buttons below.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def help_command(update, context):
    """Send help message."""
    help_text = (
        "*How to use me:*\n\n"
        "1. Send a direct message:\n"
        "   `100 USD to EUR`\n"
        "2. Use the `/convert` command:\n"
        "   `/convert 100 USD EUR`\n"
        "3. Use the interactive buttons.\n\n"
        "*Supported currencies:*\n"
        "USD, EUR, GBP, JPY, AUD, CAD, CHF, CNY, INR, BTC, and many more!\n\n"
        "*Example:*\n"
        "`50 GBP to USD`"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')

def convert_command(update, context):
    """Handle /convert command."""
    try:
        amount = float(context.args[0])
        base_currency = context.args[1].upper()
        target_currency = context.args[2].upper()
    except (IndexError, ValueError):
        update.message.reply_text(
            "❌ *Invalid format!*\n\n"
            "Usage: `/convert <amount> <from_currency> <to_currency>`\n"
            "Example: `/convert 100 USD EUR`",
            parse_mode='Markdown'
        )
        return

    rate, error = get_exchange_rate(base_currency, target_currency)
    if error:
        update.message.reply_text(f"❌ {error}")
        return

    converted_amount = amount * rate
    update.message.reply_text(
        f"💱 *Conversion Result:*\n\n"
        f"`{amount:,.2f}` {base_currency} = `{converted_amount:,.2f}` {target_currency}\n\n"
        f"📊 *Rate:* 1 {base_currency} = {rate:.4f} {target_currency}",
        parse_mode='Markdown'
    )

def handle_message(update, context):
    """Handle text messages for currency conversion."""
    text = update.message.text.strip()
    parts = text.split()
    
    if len(parts) == 4 and parts[2].lower() in ['to', 'in']:
        try:
            amount = float(parts[0])
            base_currency = parts[1].upper()
            target_currency = parts[3].upper()
        except ValueError:
            update.message.reply_text(
                "❌ *Invalid format!*\n\n"
                "Please use: `100 USD to EUR`\n"
                "or type `/help` for more options.",
                parse_mode='Markdown'
            )
            return

        rate, error = get_exchange_rate(base_currency, target_currency)
        if error:
            update.message.reply_text(f"❌ {error}")
            return

        converted_amount = amount * rate
        update.message.reply_text(
            f"💱 *Conversion Result:*\n\n"
            f"`{amount:,.2f}` {base_currency} = `{converted_amount:,.2f}` {target_currency}",
            parse_mode='Markdown'
        )
    else:
        update.message.reply_text(
            "🤔 I didn't understand that.\n\n"
            "Try sending: `100 USD to EUR`\n"
            "or type `/help` for assistance.",
            parse_mode='Markdown'
        )

def button_callback(update, context):
    """Handle button clicks."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'convert':
        query.edit_message_text(
            "💱 *How to convert:*\n\n"
            "Send me a message like:\n"
            "`100 USD to EUR`\n\n"
            "Or use the command:\n"
            "`/convert 100 USD EUR`",
            parse_mode='Markdown'
        )
    elif query.data == 'help':
        query.edit_message_text(
            "*How to use me:*\n\n"
            "1. Send a direct message:\n"
            "   `100 USD to EUR`\n"
            "2. Use the `/convert` command:\n"
            "   `/convert 100 USD EUR`\n\n"
            "*Example:*\n"
            "`50 GBP to USD`\n\n"
            "Supported currencies: USD, EUR, GBP, JPY, etc.",
            parse_mode='Markdown'
        )

def error_handler(update, context):
    """Log errors."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("convert", convert_command))
    
    # Register message handler (for text messages)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Register callback handler for buttons
    dp.add_handler(CallbackQueryHandler(button_callback))
    
    # Register error handler
    dp.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Bot is starting...")
    updater.start_polling()
    logger.info("Bot is running!")
    updater.idle()

if __name__ == '__main__':
    main()
