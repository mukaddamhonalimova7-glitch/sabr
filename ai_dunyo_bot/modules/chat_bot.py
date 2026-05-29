from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler
)
from modules.claude_client import ask_claude_with_history
from config import MAX_HISTORY, DAILY_LIMIT_PER_USER, ADMIN_IDS
from datetime import date

# Xotira (foydalanuvchi ma'lumotlari)
user_sessions = {}
daily_usage = {}

# =====================
# CHAT SYSTEM PROMPT
# =====================

CHAT_SYSTEM_PROMPT = """Siz "AI Dunyo" Telegram kanalining yordamchi botisiz (@ai_dunyo).

VAZIFANGIZ:
- Sun'iy intellekt (AI) haqida savollarga javob berish
- AI vositalarini tushuntirish va tavsiya qilish
- O'zbek tilida aniq, qisqa, foydali javoblar berish

QOIDALAR:
- FAQAT o'zbek tilida javob ber
- 200 so'zdan oshirma
- Emoji bilan qiziqarli qil
- Texnik atamalarni tushuntir
- Bilmasang — "Aniq bilmayman, lekin..." de

Kanal: @ai_dunyo"""

# =====================
# YORDAMCHI FUNKSIYALAR
# =====================

def get_history(user_id: int) -> list:
    return user_sessions.get(user_id, [])


def add_to_history(user_id: int, role: str, content: str):
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    user_sessions[user_id].append({"role": role, "content": content})
    # Faqat oxirgi N ta xabar
    if len(user_sessions[user_id]) > MAX_HISTORY * 2:
        user_sessions[user_id] = user_sessions[user_id][-MAX_HISTORY * 2:]


def check_limit(user_id: int) -> bool:
    today = str(date.today())
    if user_id not in daily_usage:
        daily_usage[user_id] = {}
    return daily_usage[user_id].get(today, 0) < DAILY_LIMIT_PER_USER


def increment_usage(user_id: int):
    today = str(date.today())
    if user_id not in daily_usage:
        daily_usage[user_id] = {}
    daily_usage[user_id][today] = daily_usage[user_id].get(today, 0) + 1


def get_usage(user_id: int) -> int:
    today = str(date.today())
    return daily_usage.get(user_id, {}).get(today, 0)

# =====================
# HANDLERS
# =====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🤖 AI nima?", callback_data="what_is_ai"),
            InlineKeyboardButton("🛠️ AI vositalar", callback_data="ai_tools"),
        ],
        [
            InlineKeyboardButton("💰 AI bilan pul topish", callback_data="ai_money"),
        ],
        [
            InlineKeyboardButton("📢 Kanal", url="https://t.me/ai_dunyo"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Salom! Men **AI Dunyo** botiman 🤖\n\n"
        "Sun'iy intellekt haqida har qanday savolingizga javob beraman!\n\n"
        "❓ Savolingizni yozing yoki tugmani bosing:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Buyruqlar:*\n\n"
        "/start — Bosh menu\n"
        "/tools — AI vositalar ro'yxati\n"
        "/clear — Suhbat tarixini tozalash\n"
        "/stats — Statistika\n\n"
        f"⚡ Kunlik limit: {DAILY_LIMIT_PER_USER} ta savol\n\n"
        "📢 Kanal: @ai\\_dunyo",
        parse_mode="Markdown"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    await update.message.reply_text("🗑️ Suhbat tarixi tozalandi! Yangi suhbat boshlashingiz mumkin.")


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠️ *Mashhur AI vositalar:*\n\n"
        "💬 *Suhbat va yozish:*\n"
        "• ChatGPT — chat.openai.com\n"
        "• Claude — claude.ai\n"
        "• Gemini — gemini.google.com\n\n"
        "🎨 *Rasm yaratish:*\n"
        "• Midjourney — midjourney.com\n"
        "• DALL·E — ChatGPT ichida\n"
        "• Canva AI — canva.com\n\n"
        "🎵 *Video va audio:*\n"
        "• Suno — suno.com (musiqa)\n"
        "• Runway — runwayml.com (video)\n\n"
        "💻 *Kod yozish:*\n"
        "• GitHub Copilot\n"
        "• Cursor — cursor.sh\n\n"
        "📢 Yangiliklari: @ai\\_dunyo",
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    used = get_usage(user_id)
    remaining = DAILY_LIMIT_PER_USER - used

    await update.message.reply_text(
        f"📊 *Statistika:*\n\n"
        f"✅ Bugun ishlatildi: {used} ta\n"
        f"⏳ Qoldi: {remaining} ta\n"
        f"📅 Limit: {DAILY_LIMIT_PER_USER} ta/kun",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asosiy xabar handleri — Claude ga yuborish"""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Limit tekshirish
    if not check_limit(user_id):
        await update.message.reply_text(
            f"⚠️ Kunlik limitga yetdingiz ({DAILY_LIMIT_PER_USER} ta savol).\n"
            "Ertaga qaytib keling! 😊\n\n"
            "📢 Yangiliklar: @ai_dunyo"
        )
        return

    # "Yozyapti..." ko'rsatish
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Tarixga qo'shish va Claude ga yuborish
    add_to_history(user_id, "user", user_text)
    history = get_history(user_id)

    response = ask_claude_with_history(
        messages=history,
        system=CHAT_SYSTEM_PROMPT
    )

    # Javobni tarixga qo'shish
    add_to_history(user_id, "assistant", response)
    increment_usage(user_id)

    # Foydalanuvchiga yuborish
    try:
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(response)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugmalar uchun handler"""
    query = update.callback_query
    await query.answer()

    responses = {
        "what_is_ai": (
            "🤖 *Sun'iy intellekt (AI) nima?*\n\n"
            "AI — kompyuterlarga inson kabi o'ylashni o'rgatish texnologiyasi.\n\n"
            "*Misollar:*\n"
            "• ChatGPT — savolga javob beradi ✍️\n"
            "• Midjourney — rasm yaratadi 🎨\n"
            "• Suno — musiqa yaratadi 🎵\n\n"
            "Hozir har bir telefonda AI bor!\n\n"
            "Boshqa savolingiz bormi?"
        ),
        "ai_tools": (
            "🛠️ *Eng mashhur BEPUL AI vositalar:*\n\n"
            "1. *ChatGPT* — chat.openai.com\n"
            "   Har qanday savol, matn yozish\n\n"
            "2. *Claude* — claude.ai\n"
            "   Uzun matnlar, tahlil\n\n"
            "3. *Canva AI* — canva.com\n"
            "   Rasm va dizayn\n\n"
            "4. *Gemini* — gemini.google.com\n"
            "   Google'ning AI yordamchisi\n\n"
            "Barchasi bepul boshlash mumkin! 🆓"
        ),
        "ai_money": (
            "💰 *AI bilan pul topish usullari:*\n\n"
            "1. *Freelance* — AI yordamida matn, rasm, kod yozish\n"
            "2. *Tarjima* — AI bilan tezroq tarjima qilish\n"
            "3. *Kontent* — blog, kanal, YouTube\n"
            "4. *Dizayn* — Canva AI bilan logo, banner\n"
            "5. *ChatBot* — bizneslar uchun bot yaratish\n\n"
            "Qaysi sohada ishlaysiz? Aniqroq maslahat beraman! 👇"
        )
    }

    text = responses.get(query.data, "Tushunmadim, iltimos qayta yozing 🤔")

    try:
        await query.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await query.message.reply_text(text)


# =====================
# HANDLERLARNI RO'YXATGA OLISH
# =====================

def register_handlers(app):
    """Barcha handlerlarni applicationga qo'shish"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("tools", tools_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
