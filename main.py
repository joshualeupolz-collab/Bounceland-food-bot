import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# -----------------------------
# Konfiguration
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = os.environ.get("RENDER_URL")  # z.B. https://bounceland-food-bot.onrender.com
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

POLL_FILE = "polls.json"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

if not BOT_TOKEN or not RENDER_URL:
    raise RuntimeError("❌ BOT_TOKEN oder RENDER_URL nicht gesetzt!")

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
        user_list = "\n".join([f"- {u}" for u in users]) if users else "–"
        text += f"*{day}*: {user_list}\n\n"
    return text

def build_keyboard(polls=None, user_name=None):
    # Optional: mark already selected buttons
    buttons = []
    for day in DAYS:
        label = day
        if polls and user_name and day in polls and user_name in polls[day]:
            label = f"✅ {day}"
        buttons.append([InlineKeyboardButton(label, callback_data=day)])
    return InlineKeyboardMarkup(buttons)

# -----------------------------
# Callback für Button-Klicks
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
    await query.edit_message_text(text=text, reply_markup=build_keyboard(polls, user), parse_mode="Markdown")

# -----------------------------
# Wochen-Umfrage posten
# -----------------------------
async def post_weekly_poll(context: ContextTypes.DEFAULT_TYPE):
    polls = {day: [] for day in DAYS}
    save_polls({"polls": polls})
    text = format_poll_text(polls)
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        reply_markup=build_keyboard(),
        parse_mode="Markdown"
    )

# -----------------------------
# Manueller /postnow Befehl
# -----------------------------
async def cmd_postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if OWNER_ID and user_id != OWNER_ID:
        await update.message.reply_text("⛔️ Only the owner can use this command.")
        return
    await post_weekly_poll(context)
    await update.message.reply_text("✅ Neue Wochenumfrage gepostet!")

# -----------------------------
# Main
# -----------------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler
    application.add_handler(CommandHandler("postnow", cmd_postnow))
    application.add_handler(CallbackQueryHandler(handle_button))

    # Webhook starten
    logging.info(f"✅ Setze Webhook: {RENDER_URL}/webhook")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{RENDER_URL}/webhook"
    )

if __name__ == "__main__":
    main()
