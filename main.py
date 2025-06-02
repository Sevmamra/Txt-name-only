from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError, TelegramError
import asyncio
import os
import random
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "7772549891:AAGDgrLy4GAa17gr2-4xa9pxWVEj8WEzrJg")
user_data = {}
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /txt to send your .txt file.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot stopping now... See you soon!")
    await app.stop()

async def txt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your .txt file now.")

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
            await update.message.reply_text("No valid messages found.")
            os.remove(file_path)
            return
        user_data[user_id] = {
            'file_path': file_path, 'batch_name': None, 'credit': None,
            'file_name': document.file_name, 'lines': lines, 'start_index': None
        }
        await update.message.reply_text(f"Total messages: {total_messages}. Send start number (1-based).")
    else:
        await update.message.reply_text("Please send a valid .txt file.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    if user_id in user_data:
        info = user_data[user_id]
        if info.get('start_index') is None:
            if not text.isdigit():
                await update.message.reply_text("Send a valid number.")
                return
            start = int(text)
            total = len(info['lines'])
            if start < 1 or start > total:
                await update.message.reply_text(f"Invalid! Enter between 1 and {total}.")
                return
            info['start_index'] = start - 1
            await update.message.reply_text("Send batch name or 1 for default.")
            return
        if info.get('batch_name') is None:
            info['batch_name'] = text if text != '1' else os.path.splitext(info['file_name'])[0].replace("_", " ")
            await update.message.reply_text("Send credit in [Name][URL] or 3 for default.")
            return
        if info.get('credit') is None:
            if text == '3':
                info['credit'] = ("𝐂𝐀 𝐈𝐧𝐭𝐞𝐫 𝐗", "https://t.me/Inter_X_Admin_Bot")
            else:
                if text.startswith('[') and '][' in text and text.endswith(']'):
                    try:
                        name, url = text[1:-1].split('][')
                        info['credit'] = (name, url)
                    except:
                        await update.message.reply_text("Invalid! Use [Name][URL].")
                        return
                else:
                    await update.message.reply_text("Invalid! Use [Name][URL].")
                    return
            await update.message.reply_text(f"🎯 Target batch {info['batch_name']}")
            for line in info['lines'][info['start_index']:]:
                try:
                    title, url = line.strip().rsplit(":", 1)
                    cname, curl = info['credit']
                    msg = f"""📝<b>Title Name ➤</b> {title}

📚<b>Batch Name ➤</b> {info['batch_name']}

📥 <b>Extracted By ➤</b> <a href="{curl}">{cname}</a>"""
                    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logging.error(f"Send error: {e}")
            await update.message.reply_text("✅ All messages sent successfully.")
            os.remove(info['file_path'])
            del user_data[user_id]

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        raise context.error
    except (NetworkError, TelegramError) as e:
        logging.warning(f"Telegram/network error: {e}")
    except Exception as e:
        logging.error(f"Unexpected: {e}")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("txt", txt_command))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
app.add_error_handler(error_handler)

if __name__ == "__main__":
    logging.info("✅ Bot is running on Render via Docker.")
    app.run_polling()
