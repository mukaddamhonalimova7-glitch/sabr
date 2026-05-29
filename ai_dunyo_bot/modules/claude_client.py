import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def ask_claude(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """Claude ga oddiy so'rov yuborish"""
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system if system else "Siz foydali yordamchisiz.",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude xatolik: {e}")
        return None


def ask_claude_with_history(messages: list, system: str = "") -> str:
    """Suhbat tarixi bilan Claude ga so'rov yuborish"""
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system if system else "Siz foydali yordamchisiz.",
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude xatolik: {e}")
        return "Kechirasiz, hozircha javob bera olmadim. Keyinroq urinib ko'ring."
