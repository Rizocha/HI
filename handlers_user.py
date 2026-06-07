from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import db, kb
from sub import check_sub
from card import movie_card

router = Router()
HTML = "HTML"

# ── Guard ─────────────────────────────────────────────────────────────────────
async def sub_gate(bot, uid, cb: CallbackQuery = None, msg: Message = None) -> bool:
    ok, missing = await check_sub(bot, uid)
    if ok:
        return True
    text = (
        "🔒 <b>Davom etish uchun quyidagi kanallarga obuna bo'ling!</b>\n\n"
        "Obuna bo'lgach <b>✅ Tekshirish</b> tugmasini bosing."
    )
    markup = kb.subscribe_kb(missing)
    if cb:
        try:
            await cb.message.edit_text(text, reply_markup=markup, parse_mode=HTML)
        except:
            await cb.message.answer(text, reply_markup=markup, parse_mode=HTML)
    elif msg:
        await msg.answer(text, reply_markup=markup, parse_mode=HTML)
    return False

# ── /start ────────────────────────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    db.ensure_user(message.from_user.id, message.from_user.full_name)

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        code = args[1].strip().upper()
        await send_movie_info(message, bot, code)
        return

    await message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        f"🎬 <b>CineBot Pro</b> — kinolarni tez va oson toping.\n\n"
        f"🔍 Kino kodini yozing yoki quyidagi menyudan tanlang:",
        reply_markup=kb.user_reply_kb(),
        parse_mode=HTML
    )
    await message.answer("📋 <b>Asosiy menyu:</b>", reply_markup=kb.main_menu_kb(), parse_mode=HTML)

# ── Inline callbacks ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "u_main")
async def cb_main(call: CallbackQuery):
    await call.message.edit_text(
        "📋 <b>Asosiy menyu:</b>",
        reply_markup=kb.main_menu_kb(), parse_mode=HTML
    )

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()

# ── Kinolar ro'yxati ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_list")
async def cb_list(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    movies = db.get_all_movies()
    if not movies:
        await call.message.edit_text("📭 Hozircha kinolar yo'q.", reply_markup=kb.back_main())
        return
    await call.message.edit_text(
        f"🎬 <b>Barcha kinolar</b> — {len(movies)} ta\n\nTanlang:",
        reply_markup=kb.movie_list_kb(movies), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("u_pg_"))
async def cb_page(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    parts = call.data.split("_")
    # format: u_pg_{page}_{prefix}_{back}
    page   = int(parts[2])
    prefix = parts[3]
    back   = "_".join(parts[4:])

    movies = db.get_all_movies()
    await call.message.edit_reply_markup(
        reply_markup=kb.movie_list_kb(movies, page=page, back=back, prefix=prefix)
    )

# ── Kino ma'lumoti ────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_info_"))
async def cb_movie_info(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    code = call.data[7:]
    await _show_movie_info(call, bot, code)

async def _show_movie_info(call: CallbackQuery, bot: Bot, code: str):
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Kino topilmadi!", show_alert=True)
        return
    uid = call.from_user.id
    favs = db.get_user(uid).get("favorites", [])
    is_fav = code in favs
    has_parts = m.get("total_parts", 1) > 1

    text = movie_card(m)
    markup = kb.movie_detail_kb(code, is_fav=is_fav, has_parts=has_parts)

    if m.get("poster_id"):
        try:
            await call.message.delete()
            await call.message.answer_photo(
                photo=m["poster_id"], caption=text,
                reply_markup=markup, parse_mode=HTML
            )
            return
        except:
            pass
    try:
        await call.message.edit_text(text, reply_markup=markup, parse_mode=HTML)
    except:
        await call.message.answer(text, reply_markup=markup, parse_mode=HTML)

# ── Kinoni yuborish ───────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_watch_"))
async def cb_watch(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    code = call.data[8:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Kino topilmadi!", show_alert=True)
        return
    await call.answer("⏳ Yuborilmoqda...")
    part_info = f" ({m['part']}/{m['total_parts']}-qism)" if m.get("total_parts", 1) > 1 else ""
    me = await bot.get_me()
    try:
        await call.message.answer_video(
            video=m["file_id"],
            caption=(
                f"🎬 <b>{m['title']}{part_info}</b>\n"
                f"📅 {m.get('year','—')} | 🎭 {m.get('category','—')}\n"
                f"🔑 Kod: <code>{code}</code>\n\n"
                f"🤖 @{me.username}"
            ),
            parse_mode=HTML
        )
        db.update_views(code)
        db.add_history(call.from_user.id, code)
        await call.message.answer(
            "✅ Kino yuborildi! Yoqdimi?",
            reply_markup=kb.after_watch_kb(code)
        )
    except Exception as e:
        await call.message.answer(f"⚠️ Yuborishda xatolik: {e}")

# ── Sevimlilar ────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_fav_"))
async def cb_fav(call: CallbackQuery):
    code = call.data[6:]
    added = db.toggle_favorite(call.from_user.id, code)
    if added:
        await call.answer("❤️ Sevimlilarga qo'shildi!", show_alert=False)
    else:
        await call.answer("💔 Sevimlidan olib tashlandi!", show_alert=False)
    # Tugmani yangilash
    m = db.get_movie(code)
    if m:
        favs = db.get_user(call.from_user.id).get("favorites", [])
        is_fav = code in favs
        has_parts = m.get("total_parts", 1) > 1
        try:
            await call.message.edit_reply_markup(
                reply_markup=kb.movie_detail_kb(code, is_fav=is_fav, has_parts=has_parts)
            )
        except:
            pass

@router.callback_query(F.data == "u_favs")
async def cb_favs(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    db.ensure_user(call.from_user.id)
    movies = db.get_favorites(call.from_user.id)
    if not movies:
        await call.message.edit_text(
            "❤️ <b>Sevimlilar</b>\n\nHozircha sevimlilar yo'q.\n"
            "Kino sahifasida ❤️ tugmasini bosing.",
            reply_markup=kb.back_main(), parse_mode=HTML
        )
        return
    await call.message.edit_text(
        f"❤️ <b>Sevimlilar</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies, back="u_main", prefix="u_info"),
        parse_mode=HTML
    )

# ── Tarix ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_history")
async def cb_history(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    db.ensure_user(call.from_user.id)
    movies = db.get_history(call.from_user.id)
    if not movies:
        await call.message.edit_text(
            "🕐 <b>Ko'rish tarixi</b>\n\nHali hech narsa ko'rmagansiz.",
            reply_markup=kb.back_main(), parse_mode=HTML
        )
        return
    await call.message.edit_text(
        f"🕐 <b>Oxirgi ko'rilganlar</b> — {len(movies)} ta:",
        reply_markup=kb.movie_list_kb(movies, back="u_main", prefix="u_info"),
        parse_mode=HTML
    )

# ── Janrlar ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_cats")
async def cb_cats(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    cats = db.get_categories()
    if not cats:
        await call.message.edit_text("📭 Janrlar yo'q.", reply_markup=kb.back_main())
        return
    await call.message.edit_text(
        "🗂 <b>Janrlar</b>\n\nQaysi janrni ko'rasiz?",
        reply_markup=kb.categories_kb(), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("u_cat_"))
async def cb_cat(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    cat = call.data[6:]
    movies = db.get_by_category(cat)
    if not movies:
        await call.message.edit_text(f"📭 <b>{cat}</b> janrida kinolar yo'q.", reply_markup=kb.back_main(), parse_mode=HTML)
        return
    await call.message.edit_text(
        f"🎭 <b>{cat}</b> — {len(movies)} ta kino:",
        reply_markup=kb.movie_list_kb(movies, back="u_cats"),
        parse_mode=HTML
    )

# ── Top 10 ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_top")
async def cb_top(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    top = db.get_top_movies(10)
    if not top:
        await call.message.edit_text("📭 Hozircha kinolar yo'q.", reply_markup=kb.back_main())
        return
    medals = ["🥇","🥈","🥉"] + [f"{i}." for i in range(4,11)]
    lines = "\n".join(
        f"{medals[i]} <b>{m['title']}</b> — {m.get('views',0):,} 👁  ⭐{db.get_avg_rating(m) or '—'}"
        for i, m in enumerate(top)
    )
    await call.message.edit_text(
        f"📊 <b>Top 10 Kinolar</b>\n\n{lines}",
        reply_markup=kb.back_main(), parse_mode=HTML
    )

# ── O'xshash kinolar ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_similar_"))
async def cb_similar(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    code = call.data[10:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    similar = db.get_similar(m)
    if not similar:
        await call.answer("😔 O'xshash kinolar topilmadi!", show_alert=True)
        return
    await call.message.edit_text(
        f"🎬 <b>'{m['title']}'</b> ga o'xshash kinolar:",
        reply_markup=kb.movie_list_kb(similar, back=f"u_info_{code}"),
        parse_mode=HTML
    )

# ── Qismlar ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_parts_"))
async def cb_parts(call: CallbackQuery, bot: Bot):
    if not await sub_gate(bot, call.from_user.id, cb=call): return
    code = call.data[8:]
    m = db.get_movie(code)
    if not m or not m.get("series_id"):
        await call.answer("📂 Qismlar topilmadi!", show_alert=True)
        return
    parts = db.get_series_parts(m["series_id"])
    await call.message.edit_text(
        f"📂 <b>{m['title'].split(' — ')[0]}</b> — barcha qismlar:",
        reply_markup=kb.parts_kb(parts, code), parse_mode=HTML
    )

# ── Reyting ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("u_rate_"))
async def cb_rate(call: CallbackQuery):
    code = call.data[7:]
    await call.message.answer(
        "⭐ <b>Kinoni baholang:</b>",
        reply_markup=kb.rating_kb(code), parse_mode=HTML
    )
    await call.answer()

@router.callback_query(F.data.startswith("u_dorate_"))
async def cb_dorate(call: CallbackQuery):
    parts = call.data.split("_")
    code  = parts[2]
    stars = int(parts[3])
    db.add_rating(code, stars)
    m = db.get_movie(code)
    avg = db.get_avg_rating(m) if m else 0
    await call.answer(f"✅ Rahmat! Bahoyingiz: {'⭐'*stars}", show_alert=True)
    try:
        await call.message.delete()
    except:
        pass

# ── Obuna tekshirish ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_checksub")
async def cb_checksub(call: CallbackQuery, bot: Bot):
    ok, missing = await check_sub(bot, call.from_user.id)
    if ok:
        await call.message.edit_text(
            "✅ <b>Obuna tasdiqlandi!</b>\n\nEndi barcha kinolarga kirish ochiq.",
            reply_markup=kb.main_menu_kb(), parse_mode=HTML
        )
    else:
        await call.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

# ── Qidiruv ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_search")
async def cb_search(call: CallbackQuery):
    db.set_state(call.from_user.id, "searching")
    await call.message.edit_text(
        "🔍 <b>Qidiruv</b>\n\nKino nomi yoki kodini yuboring:",
        reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
    )

# ── Yordam ────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "u_help")
async def cb_help(call: CallbackQuery):
    await call.message.edit_text(
        "ℹ️ <b>Yordam</b>\n\n"
        "🔢 <b>Kino kodi</b> — to'g'ridan-to'g'ri yozing (masalan <code>A101</code>)\n"
        "🔍 <b>Qidiruv</b> — kino nomini yozing\n"
        "🗂 <b>Janrlar</b> — janr bo'yicha ko'ring\n"
        "📊 <b>Top 10</b> — eng ko'p ko'rilganlar\n"
        "❤️ <b>Sevimlilar</b> — saqlab qo'yilgan kinolar\n"
        "🕐 <b>Tarix</b> — ko'rgan kinolaringiz\n"
        "⭐ <b>Baholash</b> — kinoni baholang\n"
        "📂 <b>Qismlar</b> — serial/seriya kinolar",
        reply_markup=kb.back_main(), parse_mode=HTML
    )

# ── Matn xabarlari ────────────────────────────────────────────────────────────
@router.message(F.text)
async def handle_text(message: Message, bot: Bot):
    db.ensure_user(message.from_user.id, message.from_user.full_name)
    text = message.text.strip()

    # Reply keyboard tugmalari
    if text == "🎬 Kinolar":
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        movies = db.get_all_movies()
        await message.answer(
            f"🎬 <b>Barcha kinolar</b> — {len(movies)} ta:",
            reply_markup=kb.movie_list_kb(movies), parse_mode=HTML
        )
        return
    if text == "🔍 Qidirish":
        db.set_state(message.from_user.id, "searching")
        await message.answer(
            "🔍 <b>Qidiruv</b>\n\nKino nomi yoki kodini yozing:",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return
    if text == "⭐ Sevimlilar":
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        movies = db.get_favorites(message.from_user.id)
        if not movies:
            await message.answer("❤️ Sevimlilar bo'sh.", reply_markup=kb.main_menu_kb())
            return
        await message.answer(
            f"❤️ <b>Sevimlilar</b> — {len(movies)} ta:",
            reply_markup=kb.movie_list_kb(movies), parse_mode=HTML
        )
        return
    if text == "🕐 Tarix":
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        movies = db.get_history(message.from_user.id)
        if not movies:
            await message.answer("🕐 Tarix bo'sh.", reply_markup=kb.main_menu_kb())
            return
        await message.answer(
            f"🕐 <b>Ko'rish tarixi</b> — {len(movies)} ta:",
            reply_markup=kb.movie_list_kb(movies), parse_mode=HTML
        )
        return
    if text == "🗂 Janrlar":
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        await message.answer("🗂 <b>Janrlar:</b>", reply_markup=kb.categories_kb(), parse_mode=HTML)
        return
    if text == "📊 Top 10":
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        top = db.get_top_movies(10)
        medals = ["🥇","🥈","🥉"]+[f"{i}." for i in range(4,11)]
        lines = "\n".join(
            f"{medals[i]} <b>{m['title']}</b> — {m.get('views',0):,} 👁"
            for i, m in enumerate(top)
        )
        await message.answer(f"📊 <b>Top 10</b>\n\n{lines}", reply_markup=kb.main_menu_kb(), parse_mode=HTML)
        return

    # State: qidiruv
    state = db.get_state(message.from_user.id)
    if state["s"] == "searching":
        db.clear_state(message.from_user.id)
        if not await sub_gate(bot, message.from_user.id, msg=message): return
        results = db.search_movies(text)
        if not results:
            await message.answer(
                f"🔍 <b>'{text}'</b> bo'yicha hech narsa topilmadi.\n\nBoshqa nom yoki kod kiriting:",
                reply_markup=kb.main_menu_kb(), parse_mode=HTML
            )
            return
        if len(results) == 1:
            await send_movie_info(message, bot, results[0]["code"])
            return
        await message.answer(
            f"🔍 <b>'{text}'</b> — {len(results)} ta natija:",
            reply_markup=kb.movie_list_kb(results), parse_mode=HTML
        )
        return

    # Kod bo'yicha kino
    if text.startswith("/"):
        return
    await send_movie_info(message, bot, text.upper())

async def send_movie_info(message: Message, bot: Bot, code: str):
    if not await sub_gate(bot, message.from_user.id, msg=message):
        return
    m = db.get_movie(code)
    if not m:
        # Qidiruv urinib ko'rish
        results = db.search_movies(code)
        if results:
            await message.answer(
                f"🔍 <b>'{code}'</b> bo'yicha topildi:",
                reply_markup=kb.movie_list_kb(results), parse_mode=HTML
            )
        else:
            await message.answer(
                f"❌ <b>{code}</b> kodli kino topilmadi.\n\n"
                f"💡 Kino nomini ham qidirishingiz mumkin:",
                reply_markup=kb.main_menu_kb(), parse_mode=HTML
            )
        return

    favs = db.get_user(message.from_user.id).get("favorites", [])
    is_fav = code in favs
    has_parts = m.get("total_parts", 1) > 1
    text = movie_card(m)
    markup = kb.movie_detail_kb(code, is_fav=is_fav, has_parts=has_parts)

    if m.get("poster_id"):
        try:
            await message.answer_photo(photo=m["poster_id"], caption=text, reply_markup=markup, parse_mode=HTML)
            return
        except:
            pass
    await message.answer(text, reply_markup=markup, parse_mode=HTML)
