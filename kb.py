from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
import db

# ═══════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════
def ik(*rows):
    """Shortcut: ik([btn,btn], [btn]) → InlineKeyboardMarkup"""
    return InlineKeyboardMarkup(inline_keyboard=list(rows))

def btn(text, cb=None, url=None):
    return InlineKeyboardButton(text=text, callback_data=cb, url=url)

# ═══════════════════════════════════════════════════════
#  USER  —  Reply keyboard (pastki)
# ═══════════════════════════════════════════════════════
def user_reply_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kinolar"), KeyboardButton(text="🔍 Qidirish")],
            [KeyboardButton(text="⭐ Sevimlilar"), KeyboardButton(text="🕐 Tarix")],
            [KeyboardButton(text="🗂 Janrlar"), KeyboardButton(text="📊 Top 10")],
        ],
        resize_keyboard=True,
        input_field_placeholder="🔍 Kino kodi yoki nomi..."
    )

# ═══════════════════════════════════════════════════════
#  USER  —  Inline keyboards
# ═══════════════════════════════════════════════════════
def main_menu_kb():
    return ik(
        [btn("🎬 Kinolar ro'yxati", "u_list"),   btn("🔍 Qidirish", "u_search")],
        [btn("⭐ Sevimlilar",       "u_favs"),    btn("🕐 Ko'rish tarixi", "u_history")],
        [btn("🗂 Janrlar",          "u_cats"),    btn("📊 Top 10", "u_top")],
        [btn("ℹ️ Yordam",           "u_help")],
    )

def movie_list_kb(movies, page=0, per_page=8, back="u_main", prefix="u_info"):
    s, e = page * per_page, (page + 1) * per_page
    chunk = movies[s:e]
    total = max(1, -(-len(movies) // per_page))  # ceiling div

    rows = []
    for m in chunk:
        avg = db.get_avg_rating(m)
        star = f" ⭐{avg}" if avg else ""
        part = f" [{m['part']}/{m['total_parts']}]" if m.get("total_parts", 1) > 1 else ""
        rows.append([btn(f"🎬 {m['title']}{part}{star}", f"{prefix}_{m['code']}")])

    nav = []
    if page > 0:
        nav.append(btn("◀️ Oldingi", f"u_pg_{page-1}_{prefix}_{back}"))
    nav.append(btn(f"📄 {page+1}/{total}", "noop"))
    if e < len(movies):
        nav.append(btn("Keyingi ▶️", f"u_pg_{page+1}_{prefix}_{back}"))
    if nav:
        rows.append(nav)
    rows.append([btn("🔙 Orqaga", back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def movie_detail_kb(code, is_fav=False, has_parts=False):
    fav_text = "💔 Sevimlidan chiqarish" if is_fav else "❤️ Sevimlilarga"
    rows = []
    if has_parts:
        rows.append([btn("📂 Barcha qismlar", f"u_parts_{code}")])
    rows.append([btn("▶️ Kinoni ko'rish", f"u_watch_{code}")])
    rows.append([
        btn(fav_text, f"u_fav_{code}"),
        btn("🎬 O'xshashlar", f"u_similar_{code}"),
    ])
    rows.append([
        btn("⭐ Baholash", f"u_rate_{code}"),
        btn("🔙 Orqaga", "u_list"),
    ])
    rows.append([btn("🏠 Bosh menu", "u_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def rating_kb(code):
    stars = ["⭐","⭐⭐","⭐⭐⭐","⭐⭐⭐⭐","⭐⭐⭐⭐⭐"]
    return ik(
        [btn(s, f"u_dorate_{code}_{i+1}") for i, s in enumerate(stars)],
        [btn("❌ Bekor", f"u_info_{code}")]
    )

def subscribe_kb(channels):
    rows = [[btn(f"📢 {ch['name']}", url=f"https://t.me/{ch['username'].lstrip('@')}")] for ch in channels]
    rows.append([btn("✅ Obuna bo'ldim — Tekshirish", "u_checksub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def categories_kb():
    cats = db.get_categories()
    rows = []
    row = []
    for i, c in enumerate(cats):
        row.append(btn(f"🎭 {c}", f"u_cat_{c}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([btn("🔙 Orqaga", "u_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def parts_kb(parts, current_code):
    rows = []
    for m in parts:
        mark = "▶️" if m["code"] == current_code else "📎"
        rows.append([btn(f"{mark} {m['part']}-qism — {m['title']}", f"u_watch_{m['code']}")])
    rows.append([btn("🔙 Orqaga", f"u_info_{current_code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_main():
    return ik([btn("🏠 Bosh menu", "u_main")])

def after_watch_kb(code):
    return ik(
        [btn("⭐ Baholash", f"u_rate_{code}"), btn("❤️ Sevimli", f"u_fav_{code}")],
        [btn("🎬 O'xshashlar", f"u_similar_{code}"), btn("🏠 Bosh menu", "u_main")],
    )

# ═══════════════════════════════════════════════════════
#  ADMIN  —  keyboards
# ═══════════════════════════════════════════════════════
def admin_main_kb():
    return ik(
        [btn("➕ Kino qo'shish", "a_add"),      btn("🎬 Kinolar", "a_movies")],
        [btn("📢 Kanallar",      "a_channels"),  btn("📊 Statistika", "a_stats")],
        [btn("📣 Xabar yuborish","a_broadcast"), btn("🔍 Qidirish", "a_search")],
    )

def admin_movies_kb(movies, page=0, per_page=6):
    s, e = page * per_page, (page + 1) * per_page
    chunk = movies[s:e]
    total = max(1, -(-len(movies) // per_page))

    rows = []
    for m in chunk:
        part = f"[{m['part']}/{m['total_parts']}] " if m.get("total_parts", 1) > 1 else ""
        rows.append([btn(f"🎬 {part}{m['title']}  #{m['code']}", f"a_mv_{m['code']}")])

    nav = []
    if page > 0:
        nav.append(btn("◀️", f"a_pg_{page-1}"))
    nav.append(btn(f"{page+1}/{total}", "noop"))
    if e < len(movies):
        nav.append(btn("▶️", f"a_pg_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([btn("🔙 Admin menu", "a_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_movie_detail_kb(code):
    return ik(
        [btn("✏️ Tahrirlash",    f"a_edit_{code}"),  btn("🗑 O'chirish", f"a_del_{code}")],
        [btn("📤 Ko'rish",       f"a_prev_{code}")],
        [btn("🔙 Kinolar",       "a_movies")],
    )

def admin_edit_kb(code):
    return ik(
        [btn("📝 Nom",      f"ae_title_{code}"),  btn("📅 Yil",    f"ae_year_{code}")],
        [btn("🎭 Janr",     f"ae_cat_{code}"),    btn("🌐 Til",    f"ae_lang_{code}")],
        [btn("⏱ Davomiylik",f"ae_dur_{code}"),   btn("📖 Tavsif", f"ae_desc_{code}")],
        [btn("🎞 Video",    f"ae_video_{code}"),  btn("🖼 Poster", f"ae_poster_{code}")],
        [btn("🔙 Orqaga",   f"a_mv_{code}")],
    )

def admin_confirm_del_kb(code):
    return ik(
        [btn("✅ Ha, o'chir", f"a_delok_{code}"), btn("❌ Bekor", f"a_mv_{code}")],
    )

def admin_channels_kb():
    chs = db.get_channels()
    rows = [[btn(f"📢 {c['name']}  {c['username']}", f"a_ch_{c['id']}")] for c in chs]
    rows.append([btn("➕ Kanal qo'shish", "a_addch")])
    rows.append([btn("🔙 Admin menu", "a_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_ch_detail_kb(ch_id):
    return ik(
        [btn("🗑 O'chirish", f"a_chdel_{ch_id}")],
        [btn("🔙 Kanallar",  "a_channels")],
    )

def admin_part_type_kb():
    return ik(
        [btn("🎬 Bitta kino",    "a_single"),
         btn("📂 Qisimli serial","a_series")],
        [btn("❌ Bekor",         "a_cancel")],
    )

def admin_cancel_kb():
    return ik([btn("❌ Bekor qilish", "a_cancel")])
