import logging
import asyncio
import aiohttp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "7776293126:AAF0VbXvzQ0H86EI0ThIejNHRfi89yEW2ME"
OPENROUTER_API_KEY = "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"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === MEMORY ===
user_model_choice = {}
user_memory = {}

# === MODEL BUTTONS ===
def get_model_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ChatGPT 3.5 Turbo", callback_data="model:gpt-3.5")],
        [InlineKeyboardButton("Gemini Pro", callback_data="model:gemini")]
    ])

# === AI FUNCTION ===
async def get_codegenus_reply(user_input, model_name):
    router_model_map = {
        "gpt-3.5": "openai/gpt-3.5-turbo",
        "gemini": "google/gemini-pro"
    }

    system_prompt = (
        "You are CodeGenus, a helpful and friendly assistant created by @Aymaniiiii. "
        "You can chat naturally, answer questions like a human, and when needed, help users with HTML, CSS, or JavaScript. "
        "Only provide code in those 3 languages. Avoid Python, Java, or any other programming languages."
    )

    payload = {
        "model": router_model_map.get(model_name, "openai/gpt-3.5-turbo"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:
            if resp.status != 200:
                return f"⚠️ API Error: {resp.status}"
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_model_choice[user_id] = "gpt-3.5"
    await update.message.reply_text(
        "👋 Welcome to CodeGenus!\nPlease choose a model to start:",
        reply_markup=get_model_buttons()
    )

async def handle_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    model_key = query.data.split(":")[1]

    user_model_choice[user_id] = model_key
    await query.edit_message_text(
        f"✅ Model changed to: {model_key.upper().replace('-', ' ')}\n\nNow you can chat with me or ask for HTML/CSS/JS help!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    model = user_model_choice.get(user_id, "gpt-3.5")

    if user_id not in user_memory:
        user_memory[user_id] = []
    user_memory[user_id].append(text)

    waiting = await update.message.reply_text("🤔 Thinking...")

    reply = await get_codegenus_reply(text, model)
    await waiting.edit_text(reply)

# === MAIN LOOP WITH AUTO-RECONNECT ===
async def run_bot():
    while True:
        try:
            nest_asyncio.apply()
            app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            app.add_handler(CallbackQueryHandler(handle_model_selection))
            app.add_handler(MessageHandler(filters.COMMAND, start))

            print("🤖 Bot is running...")
            await app.run_polling()
        except Exception as e:
            print(f"⚠️ Bot crashed with error: {e}\nRetrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_bot())
