import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from telegram.ext import Application

from modules.auto_poster import fetch_and_post, post_daily_digest
from modules.chat_bot import register_handlers
from config import TELEGRAM_BOT_TOKEN, POST_TIMES, POST_TIMEZONE

# =====================
# LOGGING
# =====================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TASHKENT = pytz.timezone(POST_TIMEZONE)


# =====================
# SCHEDULER — POST JADVALI
# =====================

def setup_scheduler(app: Application) -> AsyncIOScheduler:
    """Avtomatik post jadvalini sozlash"""
    scheduler = AsyncIOScheduler(timezone=TASHKENT)

    # Kuniga 3 marta yangilik post (08:00, 13:00, 19:00)
    for time_str in POST_TIMES:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            fetch_and_post,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=TASHKENT),
            kwargs={"count": 1},
            id=f"post_{time_str}",
            replace_existing=True
        )
        logger.info(f"📅 Post jadvali: {time_str} (Toshkent)")

    # Har kuni 07:55 da kunlik dayjest
    scheduler.add_job(
        post_daily_digest,
        trigger=CronTrigger(hour=7, minute=55, timezone=TASHKENT),
        id="daily_digest",
        replace_existing=True
    )
    logger.info("📅 Kunlik dayjest: 07:55 (Toshkent)")

    return scheduler


# =====================
# ASOSIY FUNKSIYA
# =====================

def main():
    logger.info("🚀 AI Dunyo Bot ishga tushmoqda...")

    # Application yaratish
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlerlarni ro'yxatga olish
    register_handlers(app)
    logger.info("✅ Handlerlar tayyor")

    # Schedulerni ishga tushirish
    scheduler = setup_scheduler(app)
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi")

    logger.info("=" * 40)
    logger.info("🤖 AI DUNYO BOT ISHGA TUSHDI!")
    logger.info(f"📢 Kanal: @ai_dunyo")
    logger.info(f"⏰ Post vaqtlari: {POST_TIMES}")
    logger.info("=" * 40)

    # Botni polling rejimida ishga tushirish
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
