import feedparser
import asyncio
import json
import os
from datetime import datetime, timedelta
from telegram import Bot
from telegram.constants import ParseMode
from modules.claude_client import ask_claude
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID, RSS_FEEDS

SEEN_FILE = "seen_articles.json"

# =====================
# YORDAMCHI FUNKSIYALAR
# =====================

def load_seen() -> set:
    """Ko'rilgan maqolalarni yuklash"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    """Ko'rilgan maqolalarni saqlash"""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


# =====================
# CLAUDE PROMPTLARI
# =====================

NEWS_SYSTEM_PROMPT = """Siz "AI Dunyo" Telegram kanalining muharriri va tarjimonisiz.
Vazifangiz: Inglizcha AI yangiliklarini professional o'zbek tiliga tarjima qilish.

QOIDALAR:
- Aniq va tushunarli o'zbek tilida yoz
- Texnik terminlarni oddiy tilda tushuntir
- Qiziqarli va jonli yoz — o'quvchi oxirigacha o'qisin
- Uzunlik: 150-200 so'z

MAJBURIY FORMAT (aynan shunday, o'zgartirma):
🔥 [SARLAVHA]

[Asosiy matn — 3 abzas]

💡 Nima uchun muhim:
[1-2 gap]

#ai_yangilik #ai_dunyo"""


DIGEST_SYSTEM_PROMPT = """Siz "AI Dunyo" Telegram kanalining bosh muharririsiz.
Kunlik AI yangiliklari dajestini o'zbek tilida tayyorlaysiz.
Qisqa, aniq, professional."""


# =====================
# ASOSIY FUNKSIYALAR
# =====================

def format_with_claude(title: str, content: str, link: str) -> str:
    """Maqolani Claude orqali o'zbek tiliga tarjima va formatlash"""

    prompt = f"""Quyidagi AI yangiliklarini o'zbek Telegram post formatiga o'tkaz:

SARLAVHA: {title}
MAZMUN: {content[:2000]}
HAVOLA: {link}

Yuqoridagi ko'rsatmalarga qat'iy amal qil."""

    result = ask_claude(prompt, system=NEWS_SYSTEM_PROMPT, max_tokens=700)

    if result:
        result += f"\n\n🔗 [To'liq o'qi]({link})"
        return result
    return None


async def fetch_and_post(count: int = 1):
    """RSS dan yangilik olib kanalga yuborish"""

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    seen = load_seen()
    posted = 0

    for feed_url in RSS_FEEDS:
        if posted >= count:
            break

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:5]:
                if posted >= count:
                    break

                article_id = entry.get("id", entry.get("link", ""))

                # Allaqachon ko'rilgan bo'lsa o'tkazish
                if article_id in seen:
                    continue

                # Faqat oxirgi 24 soatdagi yangiliklar
                published = entry.get("published_parsed")
                if published:
                    pub_date = datetime(*published[:6])
                    if datetime.utcnow() - pub_date > timedelta(hours=24):
                        continue

                title = entry.get("title", "")
                content = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")

                if not title or not link:
                    continue

                print(f"📰 Formatlash: {title[:60]}...")

                # Claude bilan tarjima va formatlash
                post_text = format_with_claude(title, content, link)

                if not post_text:
                    print("⚠️ Claude javob bermadi, o'tkazildi")
                    continue

                # Kanalga yuborish
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=False
                )

                seen.add(article_id)
                save_seen(seen)
                posted += 1

                print(f"✅ Post yuborildi: {title[:60]}")
                await asyncio.sleep(3)

        except Exception as e:
            print(f"❌ Xatolik ({feed_url}): {e}")

    print(f"📊 Jami {posted} ta post yuborildi")
    return posted


async def post_daily_digest():
    """Har kuni ertalab TOP-3 AI yangiliklari dajesti"""

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    articles = []

    for feed_url in RSS_FEEDS[:3]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                published = entry.get("published_parsed")
                if published:
                    pub_date = datetime(*published[:6])
                    if datetime.utcnow() - pub_date <= timedelta(hours=24):
                        articles.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "summary": entry.get("summary", "")[:300]
                        })
        except Exception as e:
            print(f"❌ Dayjest xatolik: {e}")

    if not articles:
        print("⚠️ Dayjest uchun maqola topilmadi")
        return

    articles_text = "\n\n".join([
        f"- {a['title']}: {a['summary']}"
        for a in articles[:5]
    ])

    digest_prompt = f"""Quyidagi AI yangiliklari asosida o'zbek tilidagi KUNLIK DAYJEST tuzing:

{articles_text}

MAJBURIY FORMAT:
🌅 BUGUNGI AI YANGILIKLARI

1️⃣ [Sarlavha]
[1-2 gap]

2️⃣ [Sarlavha]
[1-2 gap]

3️⃣ [Sarlavha]
[1-2 gap]

📌 Bugungi xulosa: [1 gap]

#ai_dunyo #bugun_ai"""

    digest = ask_claude(digest_prompt, system=DIGEST_SYSTEM_PROMPT, max_tokens=600)

    if digest:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=digest,
            parse_mode=ParseMode.MARKDOWN
        )
        print("✅ Kunlik dayjest yuborildi")
    else:
        print("⚠️ Dayjest yaratishda xatolik")
