from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hallo! Willkommen beim Bot.")

async def postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Befehl /postnow funktioniert!")
