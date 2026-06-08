from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import db, kb
from sub import check_sub

router = Router()

# ── obuna tekshiruv ───────────────────────────────────────────────────────────
async def sub_gate(bot, uid, msg=None, cb=None):
    ok, missing_tg = await check_sub(bot, uid)
    ext = db.get_ext_channels()
    # Tashqi kanallar bor yoki Telegram kanallarga obuna bo'lmagan
    if not ok or ext:
        if ok and not ext:
            return True
        text = db.get_text("sub_req")
        markup = kb.sub_kb(missing_tg, ext)
        if cb:
            try: await cb.message.edit_text(text, reply_markup=markup)
            except: await cb.message.answer(text, reply_markup=markup)
        elif msg:
            await msg.answer(text, reply_markup=markup)
        if not ok:
            return False
        # Faqat tashqi kanallar bor, Telegram OK — o'tkazib yuborish
        return True
    return True

async def sub_gate_strict(bot, uid, msg=None, cb=None):
    """Faqat Telegram obunani tekshiradi."""
    ok, missing_tg = await check_sub(bot, uid)
    if ok:
        return True
    ext = db.get_ext_channels()
    text = db.get_text("sub_req")
    markup = kb.sub_kb(missing_tg, ext)
    if cb:
        try: await cb.message.edit_text(text, reply_markup=markup)
        except: await cb.message.answer(text, reply_markup=markup)
    elif msg:
        await msg.answer(text, reply_markup=markup)
    return False

# ── video yuborish ────────────────────────────────────────────────────────────
async def send_video(target: Message, bot: Bot, code: str, uid: int):
    m = db.get_movie(code)
    if not m:
        await target.answer(db.get_text("not_found"))
        db.log_visit(uid, "not_found", code)
        return
    me = await bot.get_me()

    # Reyting
    avg   = db.auto_rating(m)
    stars = db.star_str(avg)
    rating_txt = f"{avg} ({stars})" if avg else "—"

    # Qism
    part = f" ({m['part']}/{m['total_parts']}-qism)" if m.get("total_parts",1)>1 else ""

    # Caption — rasmda ko'rsatilgan format
    cap = (
        f"🎬 <b>Nomi:</b> {m['title']}{part}\n"
        f"🆔 <b>Kodi:</b> {m['code']}\n"
        f"📅 <b>Yili:</b> {m.get('year') or '—'}\n"
        f"🎭 <b>Janri:</b> {m.get('category') or '—'}\n"
        f"🌍 <b>Tili:</b> {m.get('lang') or '—'}\n"
        f"⭐ <b>Reyting:</b> {rating_txt}\n"
        f"👁 <b>Ko\'rishlar:</b> {m.get('views',0):,}\n"
        f"\n"
        f"📝 <b>Tavsif:</b> {m.get('description') or 'Yo\'q'}\n"
        f"\n"
        f"🤖 @{me.username}"
    )
    try:
        await target.answer_video(
            video=m["file_id"], caption=cap,
            reply_markup=kb.after_video_kb(code), parse_mode="HTML"
        )
        db.inc_views(code, uid)
        db.add_history(uid, code)
        db.log_visit(uid, "watch", code)
    except Exception as e:
        await target.answer(f"⚠️ Yuborishda xatolik: {e}")

# ── /start ────────────────────────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(msg: Message, bot: Bot):
    db.ensure_user(msg.from_user.id, msg.from_user.full_name)
    db.log_visit(msg.from_user.id, "start")
    args = msg.text.split(maxsplit=1)
    if len(args) > 1:
        code = args[1].strip().upper()
        if not await sub_gate_strict(bot, msg.from_user.id, msg=msg): return
        await send_video(msg, bot, code, msg.from_user.id)
        return
    text = db.get_text("start", name=msg.from_user.first_name)
    await msg.answer(text, reply_markup=kb.user_menu(), parse_mode="HTML")

# ── checksub ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "checksub")
async def cb_checksub(call: CallbackQuery, bot: Bot):
    ok, missing = await check_sub(bot, call.from_user.id)
    if ok:
        await call.message.edit_text(db.get_text("sub_ok"))
    else:
        await call.answer("❌ Hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)

# ── utility callbacks ─────────────────────────────────────────────────────────
@router.callback_query(F.data == "main")
async def cb_main(call: CallbackQuery):
    await call.message.edit_text("Kino kodini yuboring yoki menyudan tanlang:")

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery): await call.answer()

@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery):
    db.clear_state(call.from_user.id)
    try: await call.message.delete()
    except: pass

# ── kinolar ro'yxati ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:list")
async def cb_list(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    movies = db.all_movies()
    if not movies:
        await call.message.edit_text(db.get_text("no_movies"), reply_markup=kb.back_kb()); return
    await call.message.edit_text(
        f"🎬 <b>Kinolar</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies), parse_mode="HTML"
    )

# ── sahifalash ────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("pg:"))
async def cb_pg(call: CallbackQuery):
    parts = call.data.split(":", 3)
    page = int(parts[1]); cb_prefix = parts[2]; back = parts[3]
    if cb_prefix == "play":
        movies = db.all_movies()
    elif cb_prefix.startswith("cat_"):
        movies = db.by_category(cb_prefix[4:])
    elif cb_prefix == "fav":
        movies = db.get_favs(call.from_user.id)
    elif cb_prefix == "hist":
        movies = db.get_history(call.from_user.id)
    else:
        movies = db.all_movies()
    await call.message.edit_reply_markup(
        reply_markup=kb.movie_list_kb(movies, page=page, back=back, cb_prefix=cb_prefix)
    )

# ── video yuborish (ro'yxatdan) ───────────────────────────────────────────────
@router.callback_query(F.data.startswith("play:"))
async def cb_play(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    code = call.data[5:]
    await call.answer()
    await send_video(call.message, bot, code, call.from_user.id)

# ── sevimli ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("fav:"))
async def cb_fav(call: CallbackQuery):
    code = call.data[4:]
    added = db.toggle_fav(call.from_user.id, code)
    await call.answer("❤️ Sevimlilarga qo'shildi!" if added else "💔 Sevimlidan olindi!")

# ── janrlar ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:cats")
async def cb_cats(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    if not db.categories():
        await call.message.edit_text("Janrlar yo'q.", reply_markup=kb.back_kb()); return
    await call.message.edit_text("🎭 <b>Janrlar:</b>", reply_markup=kb.cats_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat:"))
async def cb_cat(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    cat = call.data[4:]
    movies = db.by_category(cat)
    if not movies:
        await call.message.edit_text(f"<b>{cat}</b> janrida kinolar yo'q.", reply_markup=kb.back_kb("u:cats"), parse_mode="HTML"); return
    await call.message.edit_text(
        f"🎭 <b>{cat}</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies, back="u:cats", cb_prefix=f"cat_{cat}"),
        parse_mode="HTML"
    )

# ── top 10 ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:top")
async def cb_top(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    top = db.top_movies(10)
    if not top:
        await call.message.edit_text(db.get_text("no_movies"), reply_markup=kb.back_kb()); return
    lines = "\n".join(
        f"{i+1}. <b>{m['title']}</b> — {m.get('views',0):,} 👁  {db.star_str(db.auto_rating(m))}"
        for i,m in enumerate(top)
    )
    await call.message.edit_text(f"🏆 <b>Top 10</b>\n\n{lines}", reply_markup=kb.back_kb(), parse_mode="HTML")

# ── sevimlilar ────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:favs")
async def cb_favs(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    movies = db.get_favs(call.from_user.id)
    if not movies:
        await call.message.edit_text("❤️ Sevimlilar bo'sh.", reply_markup=kb.back_kb()); return
    await call.message.edit_text(
        f"❤️ <b>Sevimlilar</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies, back="main", cb_prefix="play"), parse_mode="HTML"
    )

# ── tarix ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:hist")
async def cb_hist(call: CallbackQuery, bot: Bot):
    if not await sub_gate_strict(bot, call.from_user.id, cb=call): return
    movies = db.get_history(call.from_user.id)
    if not movies:
        await call.message.edit_text("🕐 Ko'rish tarixi bo'sh.", reply_markup=kb.back_kb()); return
    await call.message.edit_text(
        f"🕐 <b>Tarix</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies, back="main", cb_prefix="play"), parse_mode="HTML"
    )

# ── qidiruv ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u:search")
async def cb_search(call: CallbackQuery):
    db.set_state(call.from_user.id, "searching")
    await call.message.edit_text("🔍 Kino nomi yoki kodini yuboring:", reply_markup=kb.cancel_kb("cancel"))

# ── matnli xabarlar ───────────────────────────────────────────────────────────
@router.message(F.text)
async def handle_text(msg: Message, bot: Bot):
    db.ensure_user(msg.from_user.id, msg.from_user.full_name)
    text = msg.text.strip()
    if text.startswith("/"): return

    # Reply keyboard tugmalari
    btn_map = {
        "🎬 Kinolar":    "list",
        "🔍 Qidirish":  "search",
        "❤️ Sevimlilar":"favs",
        "🕐 Tarix":     "hist",
        "🎭 Janrlar":   "cats",
        "🏆 Top 10":    "top",
    }
    if text in btn_map:
        action = btn_map[text]
        if action == "search":
            db.set_state(msg.from_user.id, "searching")
            await msg.answer("🔍 Kino nomi yoki kodini yuboring:", reply_markup=kb.cancel_kb("cancel"))
            return
        if not await sub_gate_strict(bot, msg.from_user.id, msg=msg): return
        db.log_visit(msg.from_user.id, action)
        if action == "list":
            movies = db.all_movies()
            if not movies: await msg.answer(db.get_text("no_movies")); return
            await msg.answer(f"🎬 <b>Kinolar</b> — {len(movies)} ta:",
                             reply_markup=kb.movie_list_kb(movies), parse_mode="HTML")
        elif action == "favs":
            movies = db.get_favs(msg.from_user.id)
            if not movies: await msg.answer("❤️ Sevimlilar bo'sh."); return
            await msg.answer(f"❤️ <b>Sevimlilar</b> — {len(movies)} ta:",
                             reply_markup=kb.movie_list_kb(movies, cb_prefix="play"), parse_mode="HTML")
        elif action == "hist":
            movies = db.get_history(msg.from_user.id)
            if not movies: await msg.answer("🕐 Tarix bo'sh."); return
            await msg.answer(f"🕐 <b>Tarix</b> — {len(movies)} ta:",
                             reply_markup=kb.movie_list_kb(movies, cb_prefix="play"), parse_mode="HTML")
        elif action == "cats":
            if not db.categories(): await msg.answer("Janrlar yo'q."); return
            await msg.answer("🎭 <b>Janrlar:</b>", reply_markup=kb.cats_kb(), parse_mode="HTML")
        elif action == "top":
            top = db.top_movies(10)
            lines = "\n".join(f"{i+1}. <b>{m['title']}</b> — {m.get('views',0):,} 👁"
                              for i,m in enumerate(top))
            await msg.answer(f"🏆 <b>Top 10</b>\n\n{lines}", parse_mode="HTML")
        return

    # Qidiruv holati
    st = db.get_state(msg.from_user.id)
    if st["s"] == "searching":
        db.clear_state(msg.from_user.id)
        if not await sub_gate_strict(bot, msg.from_user.id, msg=msg): return
        db.log_visit(msg.from_user.id, "search", text)
        results = db.search(text)
        if not results:
            await msg.answer(db.get_text("not_found")); return
        if len(results) == 1:
            await send_video(msg, bot, results[0]["code"], msg.from_user.id); return
        await msg.answer(f"🔍 <b>'{text}'</b> — {len(results)} ta natija:",
                         reply_markup=kb.movie_list_kb(results, cb_prefix="play"), parse_mode="HTML")
        return

    # Kod kiritildi
    if not await sub_gate_strict(bot, msg.from_user.id, msg=msg): return
    await send_video(msg, bot, text.upper(), msg.from_user.id)
