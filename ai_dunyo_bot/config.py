import os
from dotenv import load_dotenv

load_dotenv()

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@ai_dunyo")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# === ANTHROPIC ===
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-haiku-4-5"  # Tez va arzon

# === RSS MANBALAR ===
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://venturebeat.com/category/ai/feed/",
]

# === POST JADVALI (Toshkent vaqti) ===
POST_TIMES = ["08:00", "13:00", "19:00"]
POST_TIMEZONE = "Asia/Tashkent"

# === CHAT BOT ===
MAX_HISTORY = 10
DAILY_LIMIT_PER_USER = 20
