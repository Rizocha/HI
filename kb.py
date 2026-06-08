from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
import db

# ══════════════════════════════════════════════════════════════════════
#   USER
# ══════════════════════════════════════════════════════════════════════

def user_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎬 Kinolar"),    KeyboardButton(text="🔍 Qidirish")],
        [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="🕐 Tarix")],
        [KeyboardButton(text="🎭 Janrlar"),    KeyboardButton(text="🏆 Top 10")],
    ], resize_keyboard=True, input_field_placeholder="🎬 Kino kodini yozing...")

def sub_kb(tg_channels, ext_channels=None):
    """Majburiy obuna: Telegram + Instagram/boshqalar."""
    rows = []
    for ch in tg_channels:
        rows.append([InlineKeyboardButton(
            text=f"📢 {ch['name']}",
            url=f"https://t.me/{ch['username'].lstrip('@')}"
        )])
    for ec in (ext_channels or []):
        rows.append([InlineKeyboardButton(
            text=f"{ec['icon']} {ec['name']}",
            url=ec["url"]
        )])
    rows.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="checksub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def movie_list_kb(movies, page=0, per_page=8, back="main", cb_prefix="play"):
    s = page * per_page
    chunk = movies[s:s+per_page]
    total = max(1, -(-len(movies) // per_page))
    rows = []
    for m in chunk:
        part = f" [{m['part']}/{m['total_parts']}]" if m.get("total_parts",1)>1 else ""
        yr   = f" • {m['year']}" if m.get("year") else ""
        rows.append([InlineKeyboardButton(
            text=f"🎬 {m['title']}{part}{yr}",
            callback_data=f"{cb_prefix}:{m['code']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"pg:{page-1}:{cb_prefix}:{back}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total}", callback_data="noop"))
    if s+per_page < len(movies):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"pg:{page+1}:{cb_prefix}:{back}"))
    if nav: rows.append(nav)
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def after_video_kb(code):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❤️ Sevimli", callback_data=f"fav:{code}"),
    ]])

def cats_kb():
    cats = db.categories()
    rows = []
    row = []
    for i, c in enumerate(cats):
        row.append(InlineKeyboardButton(text=f"🎭 {c}", callback_data=f"cat:{c}"))
        if len(row) == 2: rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_kb(cb="main"):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=cb)
    ]])

def cancel_kb(cb="cancel"):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Bekor", callback_data=cb)
    ]])

# ══════════════════════════════════════════════════════════════════════
#   ADMIN
# ══════════════════════════════════════════════════════════════════════

def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo'shish",  callback_data="a:add"),
         InlineKeyboardButton(text="🎬 Kinolar",        callback_data="a:movies")],
        [InlineKeyboardButton(text="📢 Kanallar",       callback_data="a:channels"),
         InlineKeyboardButton(text="📊 Statistika",     callback_data="a:stats")],
        [InlineKeyboardButton(text="📈 Monitoring",     callback_data="a:monitor"),
         InlineKeyboardButton(text="✏️ Matnlar",        callback_data="a:texts")],
        [InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="a:broadcast"),
         InlineKeyboardButton(text="🔍 Qidirish",       callback_data="a:search")],
    ])

def admin_movies_kb(movies, page=0, per_page=6):
    s = page * per_page
    chunk = movies[s:s+per_page]
    total = max(1, -(-len(movies) // per_page))
    rows = []
    for m in chunk:
        part = f"[{m['part']}/{m['total_parts']}] " if m.get("total_parts",1)>1 else ""
        rows.append([InlineKeyboardButton(
            text=f"🎬 {part}{m['title']}  #{m['code']}",
            callback_data=f"a:mv:{m['code']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"a:pg:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if s+per_page < len(movies):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"a:pg:{page+1}"))
    if nav: rows.append(nav)
    rows.append([InlineKeyboardButton(text="🔙 Admin", callback_data="a:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_mv_kb(code):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"a:edit:{code}"),
         InlineKeyboardButton(text="🗑 O'chirish",  callback_data=f"a:del:{code}")],
        [InlineKeyboardButton(text="👁 Ko'rish",    callback_data=f"a:prev:{code}")],
        [InlineKeyboardButton(text="🔙 Kinolar",    callback_data="a:movies")],
    ])

def admin_edit_kb(code):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Nom",     callback_data=f"ae:title:{code}"),
         InlineKeyboardButton(text="📅 Yil",     callback_data=f"ae:year:{code}")],
        [InlineKeyboardButton(text="🎭 Janr",    callback_data=f"ae:cat:{code}"),
         InlineKeyboardButton(text="🌐 Til",     callback_data=f"ae:lang:{code}")],
        [InlineKeyboardButton(text="⏱ Vaqt",    callback_data=f"ae:dur:{code}"),
         InlineKeyboardButton(text="📖 Tavsif",  callback_data=f"ae:desc:{code}")],
        [InlineKeyboardButton(text="🎞 Video",   callback_data=f"ae:video:{code}"),
         InlineKeyboardButton(text="🖼 Poster",  callback_data=f"ae:poster:{code}")],
        [InlineKeyboardButton(text="🔙 Orqaga",  callback_data=f"a:mv:{code}")],
    ])

def admin_del_kb(code):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"a:delok:{code}"),
        InlineKeyboardButton(text="❌ Bekor",      callback_data=f"a:mv:{code}"),
    ]])

def admin_channels_kb():
    """Telegram + tashqi kanallar."""
    tg  = db.get_channels()
    ext = db.get_ext_channels()
    rows = []
    rows.append([InlineKeyboardButton(text="━━ Telegram ━━", callback_data="noop")])
    for c in tg:
        rows.append([InlineKeyboardButton(
            text=f"📢 {c['name']}  {c['username']}",
            callback_data=f"a:ch:tg:{c['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ Telegram kanal", callback_data="a:addch:tg")])
    rows.append([InlineKeyboardButton(text="━━ Tashqi (Instagram...) ━━", callback_data="noop")])
    for ec in ext:
        rows.append([InlineKeyboardButton(
            text=f"{ec['icon']} {ec['name']}",
            callback_data=f"a:ch:ext:{ec['url'][:30]}"
        )])
    rows.append([InlineKeyboardButton(text="➕ Instagram / boshqa", callback_data="a:addch:ext")])
    rows.append([InlineKeyboardButton(text="🔙 Admin", callback_data="a:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_ch_tg_kb(cid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"a:chdel:tg:{cid}")],
        [InlineKeyboardButton(text="🔙 Kanallar",  callback_data="a:channels")],
    ])

def admin_ch_ext_kb(url_short):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"a:chdel:ext:{url_short}")],
        [InlineKeyboardButton(text="🔙 Kanallar",  callback_data="a:channels")],
    ])

def admin_texts_kb():
    keys = {
        "start":     "🏠 Salomlashuv",
        "not_found": "❌ Kino topilmadi",
        "sub_req":   "🔒 Obuna talab",
        "sub_ok":    "✅ Obuna tasdiqlandi",
        "no_movies": "📭 Kinolar yo'q",
    }
    rows = [[InlineKeyboardButton(text=v, callback_data=f"a:txt:{k}")] for k,v in keys.items()]
    rows.append([InlineKeyboardButton(text="🔙 Admin", callback_data="a:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_part_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Bitta kino",      callback_data="a:single"),
         InlineKeyboardButton(text="📂 Qisimli serial",  callback_data="a:series")],
        [InlineKeyboardButton(text="❌ Bekor",            callback_data="a:cancel")],
    ])

def admin_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❌ Bekor", callback_data="a:cancel")
    ]])

def admin_monitor_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕐 Soatlik grafik",  callback_data="a:mon:hours"),
         InlineKeyboardButton(text="📅 Kunlik",          callback_data="a:mon:daily")],
        [InlineKeyboardButton(text="🎬 Kino statistika", callback_data="a:mon:movies"),
         InlineKeyboardButton(text="👥 Foydalanuvchilar",callback_data="a:mon:users")],
        [InlineKeyboardButton(text="🔙 Admin",           callback_data="a:main")],
    ])
