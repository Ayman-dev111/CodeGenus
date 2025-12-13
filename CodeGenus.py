import logging
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    MessageHandler, CommandHandler, filters
)

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "7776293126:AAHS9xEauPhSRzw5sBRP9XN2oihU1TwBLHU"
OPENROUTER_API_KEY = "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"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === MEMORY ===
user_memory = {}  # Stores conversation history per user
MAX_MEMORY = 15   # Keep last 15 messages per user

# === SESSION ===
session = aiohttp.ClientSession()

# === AI FUNCTION ===
async def get_codegenus_reply(user_id, user_input):
    system_prompt = (
        "You are CodeGenus, a helpful and friendly assistant created by @Aumious. "
        "You can chat naturally, answer questions like a human, and when needed, help users with HTML, CSS, or JavaScript. "
        "Only provide code in those 3 languages. Avoid Python, Java, or any other programming languages."
    )

    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    if user_id in user_memory:
        for msg in user_memory[user_id]:
            messages.append({"role": "user", "content": msg})
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": "deepseek/deepseek-v3.2",
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:
            if resp.status != 200:
                return f"⚠️ API Error: {resp.status}"
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return "⚠️ Something went wrong while contacting the AI. Please try again."

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_memory:
        user_memory[user_id] = []

    await update.message.reply_text(
        "👋 Hello! I’m CodeGenus. Let’s chat! You can ask me questions or request HTML/CSS/JS code."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(text)
    # Trim memory to last MAX_MEMORY messages
    if len(user_memory[user_id]) > MAX_MEMORY:
        user_memory[user_id] = user_memory[user_id][-MAX_MEMORY:]

    waiting = await update.message.reply_text("🤔 Thinking...")

    reply = await get_codegenus_reply(user_id, text)
    await waiting.edit_text(reply)

# === MAIN ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 CodeGenus is running with DeepSeek V3.2...")
    try:
        app.run_polling()
    finally:
        asyncio.run(session.close())
