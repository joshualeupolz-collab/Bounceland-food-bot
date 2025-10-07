import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# -----------------------------
# Konfiguration
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BOT_TOKEN or not CHAT_ID or not RENDER_URL:
    raise RuntimeError("❌ BOT_TOKEN, CHAT_ID oder RENDER_EXTERNAL_URL nicht gesetzt!")

logging.basicConfig(level=logging.INFO)

# -----------------------------
# Flask Webserver
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Poll/Keyboard
# -----------------------------
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def build_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(day, callback_data=day)] for day in DAYS])

# -----------------------------
# Telegram Handlers
# -----------------------------
async def cmd_postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"/postnow aufgerufen von {update.effective_user.first_name} ({update.effective_user.id})")
    text = "✅ Test-Umfrage gepostet!"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=build_keyboard())

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(f"Du hast {query.data} gewählt!")
    logging.info(f"{query.from_user.first_name} hat {query.data} gewählt.")

# -----------------------------
# Telegram Application
# -----------------------------
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("postnow", cmd_postnow))
application.add_handler(CallbackQueryHandler(handle_button))

# -----------------------------
# Flask Webhook Route
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@app.route("/")
def home():
    return "Bot is alive"

# -----------------------------
# Start
# -----------------------------
if __name__ == "__main__":
    # Set Telegram Webhook
    WEBHOOK_URL = RENDER_URL + "/webhook"
    logging.info(f"✅ Setze Webhook: {WEBHOOK_URL}")
    application.bot.set_webhook(WEBHOOK_URL)

    app.run(host="0.0.0.0", port=PORT)
