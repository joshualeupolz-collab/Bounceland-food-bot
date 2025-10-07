import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

# === Environment Variablen ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RENDER_URL = os.getenv("RENDER_URL")  # z. B. "https://bounceland-bot.onrender.com"

if not BOT_TOKEN or not RENDER_URL:
    raise RuntimeError("❌ BOT_TOKEN oder RENDER_URL nicht gesetzt!")

# === Flask Setup ===
app = Flask(__name__)

# === Telegram Bot Setup ===
application = Application.builder().token(BOT_TOKEN).build()


# --- Commands ---
async def start(update: Update, context):
    await update.message.reply_text("👋 Hallo! Der Webhook funktioniert ✅")


async def postnow(update: Update, context):
    await update.message.reply_text("📝 Test: /postnow funktioniert!")


# === Command-Handler hinzufügen ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("postnow", postnow))


# === Flask-Route für Telegram Webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    """Wird von Telegram aufgerufen, wenn eine Nachricht eingeht."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200


@app.route("/")
def home():
    return "🤖 Bot läuft über Webhook!", 200


# === Bot-Start (Webhook setzen) ===
async def setup_webhook():
    webhook_url = f"{RENDER_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    print(f"✅ Webhook gesetzt auf: {webhook_url}")


if __name__ == "__main__":
    import asyncio

    # Webhook setzen beim Start
    asyncio.run(setup_webhook())

    # Flask starten
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
