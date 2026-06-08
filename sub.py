from aiogram import Bot
import db

async def check_sub(bot: Bot, uid: int):
    """
    Telegram kanallarni tekshiradi.
    Tashqi havolalar (Instagram) faqat tugma sifatida ko'rsatiladi — tekshirib bo'lmaydi.
    """
    channels = db.get_channels()
    if not channels:
        return True, []
    missing = []
    for ch in channels:
        try:
            m = await bot.get_chat_member(ch["id"], uid)
            if m.status in ("left", "kicked"):
                missing.append(ch)
        except:
            pass
    return len(missing) == 0, missing
