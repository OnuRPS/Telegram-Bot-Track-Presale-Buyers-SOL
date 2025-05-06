import os
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

bot.send_message(chat_id=CHAT_ID, text="✅ Telegram bot test: funcționez corect!")
