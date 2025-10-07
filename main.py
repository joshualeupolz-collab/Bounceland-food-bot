import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
import logging
import asyncio

# Logging aktivieren
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Umgebungsvariablen
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") or "https://bounceland-bot.onrender.com"

# Flask App für Webhook-Endpoint
app = Flask(__name__)

# Telegram Application initialisieren
application = Application.builder().token(BOT_TOKEN).build()

# --- Befehle ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hallo! Ich bin dein Webhook-Bot auf Render!")

async def postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ /postnow funktioniert!")

# Handler registrieren
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("postnow", postnow))


# --- Flask Route für Telegram Updates ---
@app.route("/webhook", methods=["POST"])
def webhook():
    """Empfängt Updates von Telegram und leitet sie ans Bot-Framework weiter"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200


# --- Root Endpoint zum Testen ---
@app.route("/")
def home():
    return "🤖 Bot ist aktiv (Webhook-Version läuft auf Render)"


# --- Bot Start ---
async def set_webhook():
    """Registriert den Webhook bei Telegram"""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    logging.info(f"✅ Webhook gesetzt auf: {webhook_url}")


if __name__ == "__main__":
    # Webhook beim Start registrieren
    asyncio.run(set_webhook())

    # Flask starten (Render erkennt Port automatisch)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
