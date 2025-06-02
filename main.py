from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError, TelegramError
import asyncio
import os
import random
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot Token from environment variable or hardcode (better to use env var for Render)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Dictionary to store user data
user_data = {}

# Application instance
app = ApplicationBuilder().token(BOT_TOKEN).build()

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /txt to send your .txt file.")

# /stop Command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot stopping now... See you soon!")
    await app.stop()
    await app.shutdown()

# /txt Command
async def txt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your .txt file now.")

# Handle Document
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document

    if document.file_name.endswith('.txt'):
        file = await document.get_file()
        file_path = f"{user_id}_file.txt"
        await file.download_to_drive(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line for line in f if ':' in line]

        total_messages = len(lines)

        if total_messages == 0:
            await update.message.reply_text("No valid messages found in this file.")
            os.remove(file_path)
            return

        user_data[user_id] = {
            'file_path': file_path,
            'batch_name': None,
            'credit': None,
            'file_name': document.file_name,
            'lines': lines,
            'start_index': None
        }

        await update.message.reply_text(f"Total messages found: {total_messages}. Send from where you want to start (1-based index).")

    else:
        await update.message.reply_text("Please send a valid .txt file.")

# Handle Text Responses
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in user_data:
        user_info = user_data[user_id]

        if user_info.get('start_index') is None:
            if not text.isdigit():
                await update.message.reply_text("Please send a valid number.")
                return
            start_index = int(text)
            total = len(user_info['lines'])
            if start_index < 1 or start_index > total:
                await update.message.reply_text(f"Invalid number! Enter between 1 and {total}.")
                return

            user_data[user_id]['start_index'] = start_index - 1
            await update.message.reply_text("Send your batch name or send 1 for default.")
            return

        if user_info.get('batch_name') is None:
            if text == '1':
                file_name = user_info['file_name']
                batch_name = os.path.splitext(file_name)[0].replace("_", " ")
            else:
                batch_name = text
            user_data[user_id]['batch_name'] = batch_name
            await update.message.reply_text("Send your credit name in [Name][URL] format or send 3 for default.")
            return

        if user_info.get('credit') is None:
            if text == '3':
                credit_name = "CA Inter X"
                credit_url = "https://t.me/Inter_X_Admin_Bot"
            else:
                if text.startswith('[') and '][' in text and text.endswith(']'):
                    try:
                        credit_name, credit_url = text[1:-1].split('][')
                    except:
                        await update.message.reply_text("Invalid format! Use [Name][URL].")
                        return
                else:
                    await update.message.reply_text("Invalid format! Use [Name][URL].")
                    return

            user_data[user_id]['credit'] = (credit_name, credit_url)
            await update.message.reply_text(f"🎯 Target batch {user_info['batch_name']}")

            lines = user_info['lines']
            start_idx = user_info['start_index']

            for line in lines[start_idx:]:
                try:
                    title, url = line.strip().rsplit(":", 1)
                    credit_name, credit_url = user_info['credit']
                    message = f"""📝<b>Title Name ➤</b> {title}

📚<b>Batch Name ➤</b> {user_info['batch_name']}

📥 <b>Extracted By ➤</b> <a href="{credit_url}">{credit_name}</a>"""
                    await update.message.reply_text(message, parse_mode=ParseMode.HTML)
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logging.error(f"Error sending message: {e}")

            await update.message.reply_text("✅ All messages sent successfully. Work completed!")
            os.remove(user_info['file_path'])
            del user_data[user_id]

# Error Handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        raise context.error
    except NetworkError:
        logging.warning("Network error occurred — skipping.")
    except TelegramError as e:
        logging.error(f"Telegram error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

# Register Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("txt", txt_command))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
app.add_error_handler(error_handler)

# Run the bot
async def run_bot():
    logging.info("Bot is running on Render...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
