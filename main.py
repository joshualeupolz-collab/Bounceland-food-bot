import os
import json
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# -----------------------------
# Konfiguration
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
RENDER_URL = os.environ.get("RENDER_URL")

if not BOT_TOKEN or not RENDER_URL:
    raise RuntimeError("❌ BOT_TOKEN oder RENDER_URL nicht gesetzt!")

POLL_FILE = "polls.json"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# -----------------------------
# Flask App für Webhook
# -----------------------------
app_flask = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# -----------------------------
# Hilfsfunktionen
# -----------------------------
def load_polls():
    if not os.path.exists(POLL_FILE):
        return {}
    with open(POLL_FILE, "r") as f:
        return json.load(f)

def save_polls(polls):
    with open(POLL_FILE, "w") as f:
        json.dump(polls, f)

def format_poll_text(poll):
    text = "🍽 *Weekly Meal Participation*\n\n"
    for day, users in poll.items():
        total = len(users)
        color = "🟢" if total < 35 else "🟠" if total <= 50 else "🔴"
        user_list = "\n".join([f"- {u}" for u in users]) if users else "–"
        text += f"{color} *{day}* ({total}): {user_list}\n\n"
    return text

def build_keyboard(polls):
    buttons = []
    for day in DAYS:
        btn_text = day
        if day in polls and polls[day]:
            btn_text = f"✅ {day}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=day)])
    return InlineKeyboardMarkup(buttons)

# -----------------------------
# Button Handling
# -----------------------------
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.first_name
    day = query.data
    data = load_polls()
    polls = data.get("polls", {})

    if day not in polls:
        polls[day] = []

    if user in polls[day]:
        polls[day].remove(user)
    else:
        polls[day].append(user)

    data["polls"] = polls
    save_polls(data)
    await query.answer("✅ Updated!")
    text = format_poll_text(polls)
    await query.edit_message_text(
        text=text,
        reply_markup=build_keyboard(polls),
        parse_mode="Markdown"
    )

# -----------------------------
# /postnow Befehl
# -----------------------------
async def cmd_postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    polls = {day: [] for day in DAYS}
    save_polls({"polls": polls})
    text = format_poll_text(polls)
    await context.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=build_keyboard(polls), parse_mode="Markdown")
    await update.message.reply_text("✅ Umfrage gepostet!")

# -----------------------------
# Telegram Command / Button Handler
# -----------------------------
application.add_handler(CommandHandler("postnow", cmd_postnow))
application.add_handler(CallbackQueryHandler(handle_button))

# -----------------------------
# Flask Route für Webhook
# -----------------------------
@app_flask.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
    return "OK"

# -----------------------------
# Flask Home (Keepalive)
# -----------------------------
@app_flask.route("/")
def home():
    return "Bot is alive"

if __name__ == "__main__":
    # Webhook setzen
    import asyncio
    async def set_webhook():
        url = f"{RENDER_URL}/webhook"
        await application.bot.set_webhook(url)
        logging.info(f"✅ Webhook gesetzt: {url}")

    asyncio.run(set_webhook())
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
