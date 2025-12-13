import logging
import asyncio
import aiohttp
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)

# === CONFIG (REPLACE THESE TWO VALUES ONLY) ===
TELEGRAM_BOT_TOKEN = "7776293126:AAHS9xEauPhSRzw5sBRP9XN2oihU1TwBLHU"
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
        [InlineKeyboardButton("⚠️ Claude 3 Opus ⚠️", callback_data="model:claude")],
        [InlineKeyboardButton("Gemini Pro", callback_data="model:gemini")]
    ])

# === AI FUNCTION ===
async def get_codegenus_reply(user_input, model_name):
    if model_name == "claude":
        return (
            "⚠️ Claude 3 Opus is currently unavailable.\n\n"
            "Please choose a different model:\n\n"
            "⬇️ Available Models:\n- ChatGPT 3.5 Turbo\n- Gemini Pro"
        )

    router_model_map = {
        "gpt-3.5": "openai/gpt-3.5-turbo",
        "gemini": "google/gemini-pro"
    }

    system_prompt = (
        "You are CodeGenus, a helpful and friendly assistant created by @Aumious. "
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
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers
        ) as resp:
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

    if model_key == "claude":
        await query.edit_message_text(
            "⚠️ Claude 3 Opus is currently unavailable.\nPlease choose another model:",
            reply_markup=get_model_buttons()
        )
    else:
        user_model_choice[user_id] = model_key
        await query.edit_message_text(
            f"✅ Model changed to: {model_key.upper().replace('-', ' ')}"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    model = user_model_choice.get(user_id, "gpt-3.5")

    if user_id not in user_memory:
        user_memory[user_id] = []
    user_memory[user_id].append(text)

    thinking = await update.message.reply_text("🤔 Thinking...")
    reply = await get_codegenus_reply(text, model)
    await thinking.edit_text(reply)

# === MAIN LOOP ===
async def run_bot():
    while True:
        try:
            nest_asyncio.apply()
            app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            app.add_handler(CallbackQueryHandler(handle_model_selection))
            app.add_handler(MessageHandler(filters.COMMAND, start))

            print("🤖 CodeGenus is running...")
            await app.run_polling()
        except Exception as e:
            print(f"⚠️ Crash: {e}. Restarting in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_bot())
