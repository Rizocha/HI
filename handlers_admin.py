from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import asyncio
import db, kb
from card import movie_card
from config import ADMIN_IDS, STORAGE_CHANNEL

router = Router()
HTML = "HTML"

def is_admin(uid): return uid in ADMIN_IDS

# ── Kanalga yuklash va file_id olish ─────────────────────────────────────────
async def upload_to_channel(bot: Bot, msg: Message, caption: str = "") -> str | None:
    """
    Admindan kelgan videoni STORAGE_CHANNEL ga yuklaydi.
    Telegram o'zi file_id beradi — shu id saqlanadi.
    """
    if not STORAGE_CHANNEL:
        # Storage kanal sozlanmagan — to'g'ridan file_id ishlatiladi
        if msg.video:
            return msg.video.file_id
        if msg.document:
            return msg.document.file_id
        return None

    try:
        if msg.video:
            sent = await bot.send_video(
                chat_id=STORAGE_CHANNEL,
                video=msg.video.file_id,
                caption=caption,
                parse_mode=HTML
            )
            return sent.video.file_id

        elif msg.document:
            sent = await bot.send_document(
                chat_id=STORAGE_CHANNEL,
                document=msg.document.file_id,
                caption=caption,
                parse_mode=HTML
            )
            return sent.document.file_id

    except Exception as e:
        return None

# ── /admin ────────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat yo'q!")
        return
    s = db.get_stats()
    ch_status = "✅ Ulangan" if STORAGE_CHANNEL else "⚠️ Sozlanmagan"
    await message.answer(
        f"👑 <b>Admin Panel — CineBot Pro</b>\n\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>     🗂 Janrlar: <b>{s['categories']}</b>\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📨 Jami so'rovlar: <b>{s['requests']:,}</b>\n"
        f"📢 Kanallar: <b>{s['channels']}</b>\n"
        f"💾 Storage kanal: <b>{ch_status}</b>",
        reply_markup=kb.admin_main_kb(), parse_mode=HTML
    )

@router.callback_query(F.data == "a_main")
async def cb_admin_main(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = db.get_stats()
    ch_status = "✅ Ulangan" if STORAGE_CHANNEL else "⚠️ Sozlanmagan"
    await call.message.edit_text(
        f"👑 <b>Admin Panel</b>\n\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>     🗂 Janrlar: <b>{s['categories']}</b>\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📨 Jami so'rovlar: <b>{s['requests']:,}</b>\n"
        f"📢 Kanallar: <b>{s['channels']}</b>\n"
        f"💾 Storage kanal: <b>{ch_status}</b>",
        reply_markup=kb.admin_main_kb(), parse_mode=HTML
    )

# ── Statistika ────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_stats")
async def cb_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    s = db.get_stats()
    top_txt = "\n".join(
        f"  {i+1}. {m['title']} — {m.get('views',0):,} 👁"
        for i, m in enumerate(s["top"])
    ) or "  —"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await call.message.edit_text(
        f"📊 <b>To'liq Statistika</b>\n\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>\n"
        f"🗂 Janrlar: <b>{s['categories']}</b>\n"
        f"👥 Unikal foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📨 Jami so'rovlar: <b>{s['requests']:,}</b>\n"
        f"📢 Obuna kanallar: <b>{s['channels']}</b>\n\n"
        f"🏆 <b>Top 5 kino:</b>\n{top_txt}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Admin menu", callback_data="a_main")]
        ]),
        parse_mode=HTML
    )

# ── Kinolar ro'yxati ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_movies")
async def cb_movies(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    movies = db.get_all_movies()
    if not movies:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await call.message.edit_text(
            "📭 Hozircha kinolar yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Admin menu", callback_data="a_main")]
            ])
        )
        return
    await call.message.edit_text(
        f"🎬 <b>Kinolar</b> — {len(movies)} ta:",
        reply_markup=kb.admin_movies_kb(movies), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("a_pg_"))
async def cb_admin_pg(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    page = int(call.data[5:])
    movies = db.get_all_movies()
    await call.message.edit_reply_markup(reply_markup=kb.admin_movies_kb(movies, page=page))

# ── Kino detail (admin) ───────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("a_mv_"))
async def cb_admin_movie(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    code = call.data[5:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await call.message.edit_text(
        movie_card(m),
        reply_markup=kb.admin_movie_detail_kb(code), parse_mode=HTML
    )

# ── Preview ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("a_prev_"))
async def cb_preview(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id): return
    code = call.data[7:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await call.answer("⏳ Yuborilmoqda...")
    try:
        await call.message.answer_video(
            video=m["file_id"],
            caption=f"👁 Preview: <b>{m['title']}</b>\n🔑 Kod: <code>{code}</code>",
            parse_mode=HTML
        )
    except Exception as e:
        await call.message.answer(f"⚠️ Xatolik: {e}")

# ── O'chirish ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("a_del_"))
async def cb_del(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    code = call.data[6:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await call.message.edit_text(
        f"🗑 <b>O'chirishni tasdiqlaysizmi?</b>\n\n"
        f"🎬 <b>{m['title']}</b>\n🔑 Kod: <code>{code}</code>",
        reply_markup=kb.admin_confirm_del_kb(code), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("a_delok_"))
async def cb_delok(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    code = call.data[8:]
    if db.delete_movie(code):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await call.message.edit_text(
            f"✅ <b>{code}</b> kodli kino o'chirildi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Kinolar", callback_data="a_movies")]
            ]), parse_mode=HTML
        )
    else:
        await call.answer("❌ O'chirishda xato!", show_alert=True)

# ── Tahrirlash ────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("a_edit_"))
async def cb_edit(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    code = call.data[7:]
    m = db.get_movie(code)
    if not m:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await call.message.edit_text(
        f"✏️ <b>{m['title']}</b>\n\nNimani tahrirlaysiz?",
        reply_markup=kb.admin_edit_kb(code), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("ae_"))
async def cb_ae(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_", 2)
    field = parts[1]
    code  = parts[2]
    prompts = {
        "title":  "📝 Yangi nomni yuboring:",
        "year":   "📅 Yangi yilni yuboring:",
        "cat":    "🎭 Yangi janrni yuboring:",
        "lang":   "🌐 Tilni yuboring (Uzbek, Rus, Ingliz...):",
        "dur":    "⏱ Davomiylikni yuboring (masalan: 1:45):",
        "desc":   "📖 Yangi tavsifni yuboring:",
        "video":  "🎞 Yangi videoni yuboring (bot kanalga o'zi yuklaydi):",
        "poster": "🖼 Yangi poster rasmini yuboring:",
    }
    db.set_state(call.from_user.id, f"edit_{field}", {"code": code})
    await call.message.edit_text(
        prompts.get(field, "Yuboring:"),
        reply_markup=kb.admin_cancel_kb()
    )

# ── Kino qo'shish ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_add")
async def cb_add(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "add_type")
    storage_note = f"\n💾 Storage kanal: <code>{STORAGE_CHANNEL}</code>" if STORAGE_CHANNEL else \
                   "\n⚠️ Storage kanal sozlanmagan — file_id to'g'ridan ishlatiladi"
    await call.message.edit_text(
        f"🎬 <b>Yangi Kino Qo'shish</b>{storage_note}\n\nKino turini tanlang:",
        reply_markup=kb.admin_part_type_kb(), parse_mode=HTML
    )

@router.callback_query(F.data == "a_single")
async def cb_single(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "add_code", {"total_parts": 1, "part": 1})
    await call.message.edit_text(
        "🔑 <b>1-qadam:</b> Kino kodini kiriting\n\n"
        "📌 Misol: <code>A101</code> yoki <code>1001</code>",
        reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
    )

@router.callback_query(F.data == "a_series")
async def cb_series(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "add_series_id", {})
    await call.message.edit_text(
        "📂 <b>Qisimli Kino</b>\n\nSerial ID kiriting (barcha qismlar uchun umumiy):\n"
        "📌 Misol: <code>AVATAR</code>",
        reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
    )

# ── Kanallar ──────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_channels")
async def cb_channels(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    chs = db.get_channels()
    await call.message.edit_text(
        f"📢 <b>Obuna Kanallar</b> — {len(chs)} ta\n\n"
        f"{'Kanallar yo\'q.' if not chs else 'Boshqarish uchun tanlang:'}",
        reply_markup=kb.admin_channels_kb(), parse_mode=HTML
    )

@router.callback_query(F.data == "a_addch")
async def cb_addch(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "add_channel")
    await call.message.edit_text(
        "📢 <b>Kanal Qo'shish</b>\n\n"
        "Quyidagi formatda yuboring:\n"
        "<code>-1001234567890 | @username | Kanal Nomi</code>\n\n"
        "⚠️ Bot kanalda <b>admin</b> bo'lishi shart!",
        reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("a_ch_"))
async def cb_ch_detail(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    if call.data.startswith("a_chdel_"): return
    ch_id = call.data[5:]
    chs = db.get_channels()
    ch = next((c for c in chs if str(c["id"]) == str(ch_id)), None)
    if not ch:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    await call.message.edit_text(
        f"📢 <b>{ch['name']}</b>\n👤 {ch['username']}\n🆔 <code>{ch['id']}</code>",
        reply_markup=kb.admin_ch_detail_kb(ch_id), parse_mode=HTML
    )

@router.callback_query(F.data.startswith("a_chdel_"))
async def cb_chdel(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    ch_id = call.data[8:]
    try:
        cid = int(ch_id)
    except:
        cid = ch_id
    if db.remove_channel(cid):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await call.message.edit_text(
            "✅ Kanal o'chirildi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Kanallar", callback_data="a_channels")]
            ])
        )
    else:
        await call.answer("❌ Xato!", show_alert=True)

# ── Qidiruv ───────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_search")
async def cb_admin_search(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "a_searching")
    await call.message.edit_text(
        "🔍 Kino nomi yoki kodini yuboring:",
        reply_markup=kb.admin_cancel_kb()
    )

# ── Broadcast ─────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_broadcast")
async def cb_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.set_state(call.from_user.id, "broadcast")
    await call.message.edit_text(
        "📣 <b>Ommaviy Xabar</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni kiriting\n"
        "(Matn, rasm yoki video bo'lishi mumkin):",
        reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
    )

# ── Bekor ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "a_cancel")
async def cb_cancel(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    db.clear_state(call.from_user.id)
    s = db.get_stats()
    await call.message.edit_text(
        f"👑 <b>Admin Panel</b>\n\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📨 Jami so'rovlar: <b>{s['requests']:,}</b>",
        reply_markup=kb.admin_main_kb(), parse_mode=HTML
    )

# ═══════════════════════════════════════════════════════
#  STATE MACHINE
# ═══════════════════════════════════════════════════════
@router.message(F.text | F.video | F.document | F.photo)
async def admin_fsm(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    sd    = db.get_state(message.from_user.id)
    state = sd["s"]
    extra = sd["e"]

    if not state:
        return

    txt = message.text.strip() if message.text else ""

    if txt.lower() in ("bekor", "cancel", "/cancel"):
        db.clear_state(message.from_user.id)
        await message.answer("❌ Bekor qilindi.", reply_markup=kb.admin_main_kb())
        return

    # ── Admin qidiruv
    if state == "a_searching":
        db.clear_state(message.from_user.id)
        results = db.search_movies(txt)
        if not results:
            await message.answer("🔍 Hech narsa topilmadi.", reply_markup=kb.admin_main_kb())
            return
        await message.answer(
            f"🔍 <b>'{txt}'</b> — {len(results)} ta natija:",
            reply_markup=kb.admin_movies_kb(results), parse_mode=HTML
        )
        return

    # ── Kanal qo'shish
    if state == "add_channel":
        db.clear_state(message.from_user.id)
        try:
            p = txt.split("|")
            cid = int(p[0].strip())
            username = p[1].strip()
            name = p[2].strip()
            db.add_channel(cid, username, name)
            await message.answer(
                f"✅ <b>Kanal qo'shildi!</b>\n📢 {name}",
                reply_markup=kb.admin_channels_kb(), parse_mode=HTML
            )
        except:
            await message.answer(
                "❌ Format:\n<code>-1001234567890 | @username | Kanal Nomi</code>",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )
        return

    # ── Broadcast
    if state == "broadcast":
        db.clear_state(message.from_user.id)
        import json
        try:
            with open("data.json", "r") as f:
                all_users = json.load(f).get("users", {})
        except:
            all_users = {}
        uids = [v.get("id") for v in all_users.values() if v.get("id")]
        sent = failed = 0
        status_msg = await message.answer(f"📣 Yuborilmoqda... 0/{len(uids)}")
        for i, uid in enumerate(uids):
            try:
                if message.photo:
                    await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "", parse_mode=HTML)
                elif message.video:
                    await bot.send_video(uid, message.video.file_id, caption=message.caption or "", parse_mode=HTML)
                else:
                    await bot.send_message(uid, txt, parse_mode=HTML)
                sent += 1
            except:
                failed += 1
            if (i + 1) % 20 == 0:
                try:
                    await status_msg.edit_text(f"📣 Yuborilmoqda... {i+1}/{len(uids)}")
                except:
                    pass
            await asyncio.sleep(0.05)
        await status_msg.edit_text(
            f"✅ <b>Broadcast tugadi!</b>\n\n✔️ Yuborildi: {sent}\n❌ Xato: {failed}",
            parse_mode=HTML
        )
        return

    # ── Tahrirlash — matn maydonlar
    text_fields = {"title", "year", "cat", "lang", "dur", "desc"}
    for field in text_fields:
        if state == f"edit_{field}":
            db.clear_state(message.from_user.id)
            code = extra.get("code")
            m = db.get_movie(code)
            if not m:
                await message.answer("❌ Kino topilmadi!")
                return
            fmap = {"title":"title","year":"year","cat":"category",
                    "lang":"lang","dur":"duration","desc":"description"}
            m[fmap[field]] = txt
            db.add_movie(code, m)
            await message.answer("✅ Yangilandi!", reply_markup=kb.admin_movie_detail_kb(code))
            return

    # ── Tahrirlash — video (kanalga yuklaydi)
    if state == "edit_video":
        if not (message.video or message.document):
            await message.answer("❌ Video yuboring!", reply_markup=kb.admin_cancel_kb())
            return
        code = extra.get("code")
        m = db.get_movie(code)
        if not m:
            await message.answer("❌ Kino topilmadi!")
            return
        db.clear_state(message.from_user.id)
        wait = await message.answer("⏳ Kanalga yuklanmoqda...")
        fid = await upload_to_channel(bot, message, f"🎬 {m['title']}\n🔑 #{code}")
        if not fid:
            await wait.edit_text("❌ Yuklashda xatolik! Storage kanal tekshiring.")
            return
        m["file_id"] = fid
        db.add_movie(code, m)
        await wait.edit_text("✅ Video yangilandi va kanalga yuklandi!")
        await message.answer("", reply_markup=kb.admin_movie_detail_kb(code))
        return

    # ── Tahrirlash — poster
    if state == "edit_poster":
        if not message.photo:
            await message.answer("❌ Rasm yuboring!", reply_markup=kb.admin_cancel_kb())
            return
        code = extra.get("code")
        m = db.get_movie(code)
        if not m:
            await message.answer("❌ Kino topilmadi!")
            return
        db.clear_state(message.from_user.id)
        m["poster_id"] = message.photo[-1].file_id
        db.add_movie(code, m)
        await message.answer("✅ Poster yangilandi!", reply_markup=kb.admin_movie_detail_kb(code))
        return

    # ════════════════════════════════════════
    #  KINO QO'SHISH — bosqichli
    # ════════════════════════════════════════

    if state == "add_series_id":
        extra["series_id"] = txt.upper()
        db.set_state(message.from_user.id, "add_total_parts", extra)
        await message.answer(
            f"📂 Serial ID: <code>{txt.upper()}</code>\n\nJami qismlar soni:",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_total_parts":
        try:
            extra["total_parts"] = int(txt)
            db.set_state(message.from_user.id, "add_part_num", extra)
            await message.answer(
                f"Bu qism nechchi? (1–{int(txt)}):",
                reply_markup=kb.admin_cancel_kb()
            )
        except:
            await message.answer("❌ Faqat raqam!", reply_markup=kb.admin_cancel_kb())
        return

    if state == "add_part_num":
        try:
            extra["part"] = int(txt)
            db.set_state(message.from_user.id, "add_code", extra)
            await message.answer(
                f"🔑 Kino kodini kiriting:\n📌 Misol: <code>A101</code>",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )
        except:
            await message.answer("❌ Faqat raqam!", reply_markup=kb.admin_cancel_kb())
        return

    if state == "add_code":
        code = txt.upper()
        if db.get_movie(code):
            await message.answer(
                f"⚠️ <code>{code}</code> kodi allaqachon bor! Boshqa kod:",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )
            return
        extra["code"] = code
        db.set_state(message.from_user.id, "add_title", extra)
        await message.answer(
            f"✅ Kod: <code>{code}</code>\n\n📝 Kino nomini kiriting:",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_title":
        extra["title"] = txt
        db.set_state(message.from_user.id, "add_year", extra)
        await message.answer(
            "📅 Yilini kiriting (yoki <code>—</code> o'tkazish):",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_year":
        extra["year"] = "" if txt == "—" else txt
        db.set_state(message.from_user.id, "add_cat", extra)
        await message.answer("🎭 Janrini kiriting (Drama, Komediya, Triller...):",
                             reply_markup=kb.admin_cancel_kb())
        return

    if state == "add_cat":
        extra["category"] = "" if txt == "—" else txt
        db.set_state(message.from_user.id, "add_lang", extra)
        await message.answer(
            "🌐 Tilini kiriting (Uzbek, Rus, Ingliz... yoki <code>—</code>):",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_lang":
        extra["lang"] = "" if txt == "—" else txt
        db.set_state(message.from_user.id, "add_dur", extra)
        await message.answer(
            "⏱ Davomiyligini kiriting (masalan: 1:45 yoki <code>—</code>):",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_dur":
        extra["duration"] = "" if txt == "—" else txt
        db.set_state(message.from_user.id, "add_desc", extra)
        await message.answer(
            "📖 Qisqa tavsif kiriting (yoki <code>—</code>):",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_desc":
        extra["description"] = "" if txt == "—" else txt
        db.set_state(message.from_user.id, "add_poster", extra)
        await message.answer(
            "🖼 Poster rasmini yuboring (yoki <code>—</code> o'tkazish):",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    if state == "add_poster":
        extra["poster_id"] = ""
        if message.photo:
            extra["poster_id"] = message.photo[-1].file_id
        db.set_state(message.from_user.id, "add_video", extra)
        await message.answer(
            "🎞 <b>Endi kinoni yuboring</b>\n\n"
            "Bot uni avtomatik kanalga yuklaydi va saqlaydi 📤",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )
        return

    # ── Asosiy qadam: video kanalga yuklanadi ─────────────────────────────────
    if state == "add_video":
        if not (message.video or message.document):
            await message.answer(
                "❌ Video yuboring! (mp4, mkv, avi...)",
                reply_markup=kb.admin_cancel_kb()
            )
            return

        db.clear_state(message.from_user.id)
        code  = extra["code"]
        title = extra.get("title", "")
        part  = extra.get("part", 1)
        total = extra.get("total_parts", 1)

        part_info = f" ({part}/{total}-qism)" if total > 1 else ""

        # ── Kanalga yuklash
        wait = await message.answer(
            f"⏳ <b>Kanalga yuklanmoqda...</b>\n\n"
            f"🎬 {title}{part_info}\n"
            f"🔑 Kod: <code>{code}</code>",
            parse_mode=HTML
        )

        caption = (
            f"🎬 <b>{title}{part_info}</b>\n"
            f"📅 {extra.get('year','—')} | 🎭 {extra.get('category','—')}\n"
            f"🌐 {extra.get('lang','—')} | ⏱ {extra.get('duration','—')}\n"
            f"🔑 Kod: <code>{code}</code>"
        )

        fid = await upload_to_channel(bot, message, caption)

        if not fid:
            await wait.edit_text(
                "❌ <b>Kanalga yuklashda xatolik!</b>\n\n"
                "Tekshiring:\n"
                "• <code>STORAGE_CHANNEL</code> to'g'ri kiritilganmi?\n"
                "• Bot kanalda admin bo'lganmi?\n"
                "• Bot xabar yuborish huquqiga egami?",
                parse_mode=HTML
            )
            return

        # ── Saqlash
        movie_data = {
            "title":       title,
            "file_id":     fid,
            "category":    extra.get("category", ""),
            "description": extra.get("description", ""),
            "year":        extra.get("year", ""),
            "lang":        extra.get("lang", ""),
            "duration":    extra.get("duration", ""),
            "part":        part,
            "total_parts": total,
            "series_id":   extra.get("series_id", ""),
            "poster_id":   extra.get("poster_id", ""),
        }
        db.add_movie(code, movie_data)

        await wait.edit_text(
            f"✅ <b>Kino qo'shildi va kanalga yuklandi!</b>\n\n"
            f"🎬 <b>{title}{part_info}</b>\n"
            f"🔑 Kod: <code>{code}</code>\n"
            f"📅 {extra.get('year','—')} | 🎭 {extra.get('category','—')}\n"
            f"🌐 {extra.get('lang','—')} | ⏱ {extra.get('duration','—')}\n\n"
            f"💾 File kanalda saqlanmoqda — server restart bo'lsa ham yo'qolmaydi!",
            reply_markup=kb.admin_main_kb(), parse_mode=HTML
        )
        return
