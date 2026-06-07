import db

LANG_FLAGS = {
    "uzbek": "\U0001f1fa\U0001f1ff", "o'zbek": "\U0001f1fa\U0001f1ff",
    "rus": "\U0001f1f7\U0001f1fa", "russian": "\U0001f1f7\U0001f1fa",
    "ingliz": "\U0001f1fa\U0001f1f8", "english": "\U0001f1fa\U0001f1f8",
    "turk": "\U0001f1f9\U0001f1f7", "turkish": "\U0001f1f9\U0001f1f7",
    "hind": "\U0001f1ee\U0001f1f3", "hindi": "\U0001f1ee\U0001f1f3",
    "koreya": "\U0001f1f0\U0001f1f7", "korean": "\U0001f1f0\U0001f1f7",
}

def lang_flag(lang: str) -> str:
    return LANG_FLAGS.get(lang.lower(), "\U0001f310") if lang else ""

def star_bar(rating: float) -> str:
    if not rating:
        return "\u2606\u2606\u2606\u2606\u2606"
    full = int(round(rating))
    return "\u2b50" * full + "\u2606" * (5 - full)

def movie_card(m: dict, short=False) -> str:
    avg   = db.get_avg_rating(m)
    stars = star_bar(avg)
    rating_text = (
        f"{stars} {avg}/5 ({m.get('rating_count', 0)} baho)"
        if avg else f"{stars} Hali baholanmagan"
    )

    part_line = ""
    if m.get("total_parts", 1) > 1:
        part_line = f"\n\U0001f4c2 <b>Qism:</b> {m['part']}/{m['total_parts']}"

    lang = m.get("lang", "")
    lang_line = f"\n\U0001f310 <b>Til:</b> {lang_flag(lang)} {lang}" if lang else ""

    dur = m.get("duration", "")
    dur_line = f"\n\u23f1 <b>Davomiylik:</b> {dur}" if dur else ""

    no_desc = "<i>Tavsif qo\u02bbshilmagan</i>"

    if short:
        return (
            f"\U0001f3ac <b>{m['title']}</b>{part_line}\n"
            f"\u2501" * 24 + "\n"
            f"\U0001f4c5 <b>Yil:</b> {m.get('year', '\u2014')}{lang_line}\n"
            f"\U0001f3ad <b>Janr:</b> {m.get('category', '\u2014')}\n"
            f"\u2b50 <b>Reyting:</b> {rating_text}\n"
            f"\U0001f511 <b>Kod:</b> <code>{m['code']}</code>"
        )

    desc = m.get("description") or no_desc
    line = "\u2501" * 24

    return (
        f"\U0001f3ac <b>{m['title']}</b>{part_line}\n"
        f"{line}\n"
        f"\U0001f4c5 <b>Yil:</b> {m.get('year', '\u2014')}{lang_line}{dur_line}\n"
        f"\U0001f3ad <b>Janr:</b> {m.get('category', '\u2014')}\n"
        f"\U0001f441 <b>Ko\u02bbrishlar:</b> {m.get('views', 0):,}\n"
        f"\u2b50 <b>Reyting:</b> {rating_text}\n"
        f"{line}\n"
        f"\U0001f4d6 {desc}\n"
        f"{line}\n"
        f"\U0001f511 <b>Kod:</b> <code>{m['code']}</code>"
    )
