from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import asyncio
import db, kb
from config import ADMIN_IDS, STORAGE_CHANNEL

router = Router()
HTML = "HTML"

def is_admin(uid): return uid in ADMIN_IDS

# ── kanalga yuklash ───────────────────────────────────────────────────────────
async def upload(bot: Bot, msg: Message, caption=""):
    if not STORAGE_CHANNEL:
        if msg.video: return msg.video.file_id
        if msg.document: return msg.document.file_id
        return None
    try:
        if msg.video:
            s = await bot.send_video(STORAGE_CHANNEL, msg.video.file_id, caption=caption, parse_mode=HTML)
            return s.video.file_id
        if msg.document:
            s = await bot.send_document(STORAGE_CHANNEL, msg.document.file_id, caption=caption, parse_mode=HTML)
            return s.document.file_id
    except:
        return None

# ── kino karta matni ──────────────────────────────────────────────────────────
def mv_text(m):
    avg   = db.auto_rating(m)
    stars = db.star_str(avg)
    viewers = len(m.get("viewers", []))
    part_line = f"\n📂 <b>Qism:</b> {m['part']}/{m['total_parts']}" if m.get("total_parts",1)>1 else ""
    return (
        f"🎬 <b>Nomi:</b> {m['title']}{part_line}\n"
        f"🆔 <b>Kodi:</b> {m['code']}\n"
        f"📅 <b>Yili:</b> {m.get('year') or '—'}\n"
        f"🎭 <b>Janri:</b> {m.get('category') or '—'}\n"
        f"🌍 <b>Tili:</b> {m.get('lang') or '—'}\n"
        f"⏱ <b>Vaqti:</b> {m.get('duration') or '—'}\n"
        f"⭐ <b>Reyting:</b> {avg if avg else '—'} ({stars})\n"
        f"👁 <b>Ko\'rishlar:</b> {m.get('views',0):,}\n"
        f"👤 <b>Unique viewers:</b> {viewers:,}\n\n"
        f"📝 <b>Tavsif:</b> {m.get('description') or 'Yo\'q'}"
    )

# ── statistika matni ──────────────────────────────────────────────────────────
def stat_text():
    s = db.stats()
    top_lines = []
    for i, m in enumerate(s["top5"]):
        avg = db.auto_rating(m)
        stars = db.star_str(avg)
        top_lines.append(f"  {i+1}. {m['title']} — {m.get('views',0):,} 👁 {stars}")
    top = "\n".join(top_lines) or "  —"
    peak = f"{s['peak_hour']}:00–{s['peak_hour']+1}:00 ({s['peak_count']} so'rov)" if s.get("peak_hour") is not None else "—"
    return (
        f"📊 <b>Statistika</b>\n\n"
        f"🎬 Kinolar: <b>{s['movies']}</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📨 Jami so'rovlar: <b>{s['requests']:,}</b>\n"
        f"📢 Kanallar: <b>{s['channels']}</b>\n"
        f"🔗 Tashqi havolalar: <b>{s['ext_ch']}</b>\n\n"
        f"📅 <b>Bugun:</b> {s['today']} so'rov | {s['today_users']} foydalanuvchi\n"
        f"⚡ <b>Eng faol soat:</b> {peak}\n\n"
        f"🏆 <b>Top 5:</b>\n{top}"
    )

# ── soatlik grafik matni ──────────────────────────────────────────────────────
def hours_text():
    hours = db.get_hourly_chart()
    if not any(hours.values()):
        return "📊 Bugun hali so'rovlar yo'q."
    max_val = max(hours.values()) or 1
    lines = []
    for h in range(24):
        cnt = hours.get(h, 0)
        bar_len = int(cnt / max_val * 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        lines.append(f"`{h:02d}:00` {bar} {cnt}")
    return "🕐 <b>Bugungi soatlik faollik</b>\n\n" + "\n".join(lines)

# ── /admin ────────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Ruxsat yo'q!"); return
    await msg.answer(stat_text(), reply_markup=kb.admin_main_kb(), parse_mode=HTML)

# ── barcha admin callbacklar ──────────────────────────────────────────────────
@router.callback_query(F.data.startswith("a:"))
async def admin_cb(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id): return
    raw = call.data[2:]
    parts = raw.split(":", 2)
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""

    # ── bosh sahifa
    if cmd == "main":
        await call.message.edit_text(stat_text(), reply_markup=kb.admin_main_kb(), parse_mode=HTML)

    # ── kinolar
    elif cmd == "movies":
        mvs = db.all_movies()
        if not mvs:
            await call.message.edit_text("📭 Kinolar yo'q.", reply_markup=kb.admin_main_kb()); return
        await call.message.edit_text(f"🎬 <b>Kinolar</b> — {len(mvs)} ta:",
                                      reply_markup=kb.admin_movies_kb(mvs), parse_mode=HTML)

    elif cmd == "pg":
        mvs = db.all_movies()
        await call.message.edit_reply_markup(reply_markup=kb.admin_movies_kb(mvs, page=int(arg)))

    elif cmd == "mv":
        m = db.get_movie(arg)
        if not m: await call.answer("❌ Topilmadi!", show_alert=True); return
        await call.message.edit_text(mv_text(m), reply_markup=kb.admin_mv_kb(arg), parse_mode=HTML)

    elif cmd == "prev":
        m = db.get_movie(arg)
        if not m: await call.answer("❌ Topilmadi!", show_alert=True); return
        await call.answer("⏳ Yuborilmoqda...")
        try:
            await call.message.answer_video(
                video=m["file_id"],
                caption=f"👁 Preview: <b>{m['title']}</b>", parse_mode=HTML
            )
        except Exception as e:
            await call.message.answer(f"⚠️ {e}")

    elif cmd == "del":
        m = db.get_movie(arg)
        if not m: await call.answer("❌ Topilmadi!", show_alert=True); return
        await call.message.edit_text(
            f"🗑 <b>O'chirasizmi?</b>\n\n🎬 {m['title']}\n🔑 <code>{arg}</code>",
            reply_markup=kb.admin_del_kb(arg), parse_mode=HTML)

    elif cmd == "delok":
        if db.delete_movie(arg):
            await call.message.edit_text("✅ Kino o'chirildi!", reply_markup=kb.admin_main_kb())
        else:
            await call.answer("❌ Xato!", show_alert=True)

    elif cmd == "edit":
        m = db.get_movie(arg)
        if not m: await call.answer("❌ Topilmadi!", show_alert=True); return
        await call.message.edit_text(f"✏️ <b>{m['title']}</b>\n\nNimani tahrirlaysiz?",
                                      reply_markup=kb.admin_edit_kb(arg), parse_mode=HTML)

    # ── statistika
    elif cmd == "stats":
        await call.message.edit_text(stat_text(), reply_markup=kb.admin_main_kb(), parse_mode=HTML)

    # ── monitoring
    elif cmd == "monitor":
        mon = db.get_monitoring_summary()
        if not mon:
            await call.message.edit_text("📈 Hali monitoring ma'lumoti yo'q.",
                                          reply_markup=kb.admin_monitor_kb()); return
        dates_txt = "\n".join(
            f"  📅 {dt}: {cnt} so'rov" for dt, cnt in mon["recent_dates"]
        )
        peak = f"{mon['peak_hour']}:00–{mon['peak_hour']+1}:00 ({mon['peak_count']} so'rov)" \
               if mon["peak_hour"] is not None else "—"
        text = (
            f"📈 <b>Monitoring</b>\n\n"
            f"📊 Jami loglangan: {mon['total_logs']:,}\n\n"
            f"📅 <b>Bugun:</b> {mon['today']} so'rov\n"
            f"👤 <b>Bugungi unique users:</b> {mon['today_users']}\n"
            f"📉 <b>Kecha:</b> {mon['yesterday']} so'rov\n"
            f"⚡ <b>Eng faol soat:</b> {peak}\n\n"
            f"📆 <b>So'nggi kunlar:</b>\n{dates_txt}"
        )
        await call.message.edit_text(text, reply_markup=kb.admin_monitor_kb(), parse_mode=HTML)

    elif cmd == "mon":
        # arg = hours / daily / movies / users
        if arg == "hours":
            await call.message.edit_text(
                hours_text(), reply_markup=kb.admin_monitor_kb(), parse_mode=HTML
            )
        elif arg == "daily":
            mon = db.get_monitoring_summary()
            if not mon:
                await call.message.edit_text("Ma'lumot yo'q.", reply_markup=kb.admin_monitor_kb()); return
            dates_txt = "\n".join(
                f"  📅 {dt}: {cnt} so'rov" for dt, cnt in mon["recent_dates"]
            )
            await call.message.edit_text(
                f"📅 <b>Kunlik statistika (7 kun)</b>\n\n{dates_txt}",
                reply_markup=kb.admin_monitor_kb(), parse_mode=HTML
            )
        elif arg == "movies":
            mvs = sorted(db.all_movies(), key=lambda x: x.get("views",0), reverse=True)[:10]
            lines = "\n".join(
                f"  {i+1}. <b>{m['title']}</b>\n"
                f"     👁 {m.get('views',0):,} ko'rish | 👤 {len(m.get('viewers',[]))} unique"
                for i,m in enumerate(mvs)
            )
            await call.message.edit_text(
                f"🎬 <b>Kino Ko'rishlar Statistikasi</b>\n\n{lines or '—'}",
                reply_markup=kb.admin_monitor_kb(), parse_mode=HTML
            )
        elif arg == "users":
            users = db.all_users()
            active = sorted(users, key=lambda x: x.get("requests",0), reverse=True)[:10]
            lines = "\n".join(
                f"  {i+1}. {u.get('name','?')} — {u.get('requests',0)} so'rov | {u.get('joined','')}"
                for i,u in enumerate(active)
            )
            await call.message.edit_text(
                f"👥 <b>Faol Foydalanuvchilar</b>\n\nJami: {len(users)}\n\n{lines or '—'}",
                reply_markup=kb.admin_monitor_kb(), parse_mode=HTML
            )

    # ── kanallar
    elif cmd == "channels":
        tg = db.get_channels(); ext = db.get_ext_channels()
        await call.message.edit_text(
            f"📢 <b>Kanallar</b>\n\nTelegram: {len(tg)} | Tashqi: {len(ext)}",
            reply_markup=kb.admin_channels_kb(), parse_mode=HTML
        )

    elif cmd == "addch":
        # arg = tg / ext
        if arg == "tg":
            db.set_state(call.from_user.id, "add_ch_tg")
            await call.message.edit_text(
                "📢 <b>Telegram Kanal Qo'shish</b>\n\n"
                "Formatda yuboring:\n"
                "<code>-1001234567890 | @username | Kanal Nomi</code>\n\n"
                "⚠️ Bot kanalda admin bo'lishi shart!",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )
        elif arg == "ext":
            db.set_state(call.from_user.id, "add_ch_ext")
            await call.message.edit_text(
                "🔗 <b>Tashqi Havola Qo'shish</b>\n\n"
                "Formatda yuboring:\n"
                "<code>Instagram | https://instagram.com/sizning_sahifa | 📸</code>\n\n"
                "Icon: 📸 Instagram | 🎥 YouTube | 🌐 Website | 📱 TikTok",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )

    elif cmd == "ch":
        # arg = tg/ext, arg2 = id/url
        if arg == "tg":
            chs = db.get_channels()
            ch = next((c for c in chs if str(c["id"]) == str(arg2)), None)
            if not ch: await call.answer("❌ Topilmadi!", show_alert=True); return
            await call.message.edit_text(
                f"📢 <b>{ch['name']}</b>\n{ch['username']}\n<code>{ch['id']}</code>",
                reply_markup=kb.admin_ch_tg_kb(arg2), parse_mode=HTML
            )
        elif arg == "ext":
            ext = db.get_ext_channels()
            ec = next((c for c in ext if c["url"][:30] == arg2), None)
            if not ec: await call.answer("❌ Topilmadi!", show_alert=True); return
            await call.message.edit_text(
                f"{ec['icon']} <b>{ec['name']}</b>\n{ec['url']}",
                reply_markup=kb.admin_ch_ext_kb(arg2), parse_mode=HTML
            )

    elif cmd == "chdel":
        # arg = tg/ext, arg2 = id/url_short
        if arg == "tg":
            try: cid = int(arg2)
            except: cid = arg2
            if db.remove_channel(cid):
                await call.message.edit_text("✅ Telegram kanal o'chirildi!",
                                              reply_markup=kb.admin_channels_kb())
            else:
                await call.answer("❌ Xato!", show_alert=True)
        elif arg == "ext":
            ext = db.get_ext_channels()
            ec = next((c for c in ext if c["url"][:30] == arg2), None)
            if ec and db.remove_ext_channel(ec["url"]):
                await call.message.edit_text("✅ Tashqi havola o'chirildi!",
                                              reply_markup=kb.admin_channels_kb())
            else:
                await call.answer("❌ Xato!", show_alert=True)

    # ── matnlar
    elif cmd == "texts":
        texts = db.get_all_texts()
        lines = "\n\n".join(f"<b>{k}:</b>\n{v}" for k,v in texts.items())
        await call.message.edit_text(
            f"✏️ <b>Bot Matnlari</b>\n\n{lines}",
            reply_markup=kb.admin_texts_kb(), parse_mode=HTML
        )

    elif cmd == "txt":
        key_names = {"start":"Salomlashuv","not_found":"Kino topilmadi",
                     "sub_req":"Obuna talab","sub_ok":"Obuna tasdiqlandi","no_movies":"Kinolar yo'q"}
        db.set_state(call.from_user.id, "edit_text", {"key": arg})
        cur = db.get_text(arg)
        await call.message.edit_text(
            f"✏️ <b>{key_names.get(arg, arg)}</b>\n\n"
            f"Hozirgi:\n<i>{cur}</i>\n\n"
            f"Yangi matnni yuboring:\n"
            f"💡 <code>{{name}}</code> — ism (faqat start uchun)",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )

    # ── broadcast
    elif cmd == "broadcast":
        db.set_state(call.from_user.id, "broadcast")
        await call.message.edit_text(
            "📣 <b>Ommaviy Xabar</b>\n\nBarcha foydalanuvchilarga xabar yuboring:",
            reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
        )

    # ── qidiruv
    elif cmd == "search":
        db.set_state(call.from_user.id, "a_search")
        await call.message.edit_text("🔍 Kino nomi yoki kodini yuboring:",
                                      reply_markup=kb.admin_cancel_kb())

    # ── kino qo'shish
    elif cmd == "add":
        db.set_state(call.from_user.id, "add_type")
        st = "✅ Ulangan" if STORAGE_CHANNEL else "⚠️ Sozlanmagan"
        await call.message.edit_text(
            f"➕ <b>Kino Qo'shish</b>\n💾 Storage: {st}\n\nKino turini tanlang:",
            reply_markup=kb.admin_part_kb(), parse_mode=HTML
        )

    elif cmd == "single":
        db.set_state(call.from_user.id, "add_code", {"total_parts":1,"part":1})
        await call.message.edit_text("🔑 Kino kodini kiriting (masalan: <code>101</code>):",
                                      reply_markup=kb.admin_cancel_kb(), parse_mode=HTML)

    elif cmd == "series":
        db.set_state(call.from_user.id, "add_sid", {})
        await call.message.edit_text("📂 Serial ID kiriting (masalan: <code>AVATAR</code>):",
                                      reply_markup=kb.admin_cancel_kb(), parse_mode=HTML)

    elif cmd == "cancel":
        db.clear_state(call.from_user.id)
        await call.message.edit_text(stat_text(), reply_markup=kb.admin_main_kb(), parse_mode=HTML)

# ── ae: tahrirlash ────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("ae:"))
async def admin_ae(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    parts = call.data.split(":", 2)
    field = parts[1]; code = parts[2]
    prompts = {
        "title":"📝 Yangi nomni yuboring:","year":"📅 Yangi yilni yuboring:",
        "cat":"🎭 Yangi janrni yuboring:","lang":"🌐 Tilni yuboring:",
        "dur":"⏱ Davomiylikni yuboring (1:45):","desc":"📖 Yangi tavsifni yuboring:",
        "video":"🎞 Yangi videoni yuboring (kanalga yuklanadi):","poster":"🖼 Yangi poster yuboring:",
    }
    db.set_state(call.from_user.id, f"edit_{field}", {"code": code})
    await call.message.edit_text(prompts.get(field,"Yuboring:"), reply_markup=kb.admin_cancel_kb())

# ── noop ─────────────────────────────────────────────────────────────────────
@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery): await call.answer()

# ══════════════════════════════════════════════════════════════════════
#   STATE MACHINE — faqat admin + aktiv state bo'lganda ishlaydi
# ══════════════════════════════════════════════════════════════════════
from aiogram.filters import Filter

class AdminStateFilter(Filter):
    async def __call__(self, msg: Message) -> bool:
        if not is_admin(msg.from_user.id):
            return False
        sd = db.get_state(msg.from_user.id)
        return sd["s"] is not None

@router.message(AdminStateFilter(), F.text | F.video | F.document | F.photo)
async def admin_fsm(msg: Message, bot: Bot):
    sd = db.get_state(msg.from_user.id)
    state = sd["s"]; extra = sd["e"]
    if not state: return
    txt = msg.text.strip() if msg.text else ""

    if txt.lower() in ("bekor", "/cancel"):
        db.clear_state(msg.from_user.id)
        await msg.answer("❌ Bekor.", reply_markup=kb.admin_main_kb()); return

    # ── matn tahrirlash
    if state == "edit_text":
        db.clear_state(msg.from_user.id)
        db.set_text(extra["key"], txt)
        await msg.answer("✅ Matn yangilandi!", reply_markup=kb.admin_main_kb()); return

    # ── Telegram kanal qo'shish
    if state == "add_ch_tg":
        db.clear_state(msg.from_user.id)
        try:
            p = [x.strip() for x in txt.split("|")]
            db.add_channel(int(p[0]), p[1], p[2])
            await msg.answer(f"✅ Telegram kanal qo'shildi: <b>{p[2]}</b>",
                             reply_markup=kb.admin_channels_kb(), parse_mode=HTML)
        except:
            await msg.answer("❌ Format:\n<code>-100xxx | @username | Nom</code>",
                             reply_markup=kb.admin_cancel_kb(), parse_mode=HTML)
        return

    # ── Tashqi havola qo'shish (Instagram, YouTube...)
    if state == "add_ch_ext":
        db.clear_state(msg.from_user.id)
        try:
            p = [x.strip() for x in txt.split("|")]
            name = p[0]; url = p[1]
            icon = p[2] if len(p) > 2 else "🔗"
            db.add_ext_channel(name, url, icon)
            await msg.answer(f"✅ Havola qo'shildi: {icon} <b>{name}</b>",
                             reply_markup=kb.admin_channels_kb(), parse_mode=HTML)
        except:
            await msg.answer(
                "❌ Format:\n<code>Instagram | https://instagram.com/sizning_sahifa | 📸</code>",
                reply_markup=kb.admin_cancel_kb(), parse_mode=HTML
            )
        return

    # ── broadcast
    if state == "broadcast":
        db.clear_state(msg.from_user.id)
        users = db.all_users()
        sent = failed = 0
        sm = await msg.answer(f"📣 Yuborilmoqda... 0/{len(users)}")
        for i, u in enumerate(users):
            uid = u.get("id")
            if not uid: continue
            try:
                if msg.photo:
                    await bot.send_photo(uid, msg.photo[-1].file_id,
                                         caption=msg.caption or "", parse_mode=HTML)
                elif msg.video:
                    await bot.send_video(uid, msg.video.file_id,
                                         caption=msg.caption or "", parse_mode=HTML)
                else:
                    await bot.send_message(uid, txt, parse_mode=HTML)
                sent += 1
            except: failed += 1
            if (i+1) % 20 == 0:
                try: await sm.edit_text(f"📣 {i+1}/{len(users)}")
                except: pass
            await asyncio.sleep(0.05)
        await sm.edit_text(f"✅ Tugadi!\n✔️ Yuborildi: {sent}\n❌ Xato: {failed}")
        return

    # ── admin qidiruv
    if state == "a_search":
        db.clear_state(msg.from_user.id)
        res = db.search(txt)
        if not res: await msg.answer("🔍 Topilmadi.", reply_markup=kb.admin_main_kb()); return
        await msg.answer(f"🔍 {len(res)} ta natija:", reply_markup=kb.admin_movies_kb(res)); return

    # ── matn field tahrirlash
    field_map = {"title":"title","year":"year","cat":"category","lang":"lang",
                 "dur":"duration","desc":"description"}
    for sf, df in field_map.items():
        if state == f"edit_{sf}":
            db.clear_state(msg.from_user.id)
            code = extra.get("code"); m = db.get_movie(code)
            if not m: await msg.answer("❌ Topilmadi!"); return
            m[df] = txt; db.add_movie(code, m)
            await msg.answer("✅ Yangilandi!", reply_markup=kb.admin_mv_kb(code)); return

    # ── video tahrirlash
    if state == "edit_video":
        if not (msg.video or msg.document):
            await msg.answer("❌ Video yuboring!", reply_markup=kb.admin_cancel_kb()); return
        code = extra.get("code"); m = db.get_movie(code)
        if not m: await msg.answer("❌ Topilmadi!"); return
        db.clear_state(msg.from_user.id)
        w = await msg.answer("⏳ Kanalga yuklanmoqda...")
        fid = await upload(bot, msg, f"🎬 {m['title']}\n🔑 #{code}")
        if not fid: await w.edit_text("❌ Yuklashda xatolik!"); return
        m["file_id"] = fid; db.add_movie(code, m)
        await w.edit_text("✅ Video yangilandi!", reply_markup=kb.admin_mv_kb(code)); return

    # ── poster tahrirlash
    if state == "edit_poster":
        if not msg.photo:
            await msg.answer("❌ Rasm yuboring!", reply_markup=kb.admin_cancel_kb()); return
        code = extra.get("code"); m = db.get_movie(code)
        if not m: await msg.answer("❌ Topilmadi!"); return
        db.clear_state(msg.from_user.id)
        m["poster_id"] = msg.photo[-1].file_id; db.add_movie(code, m)
        await msg.answer("✅ Poster yangilandi!", reply_markup=kb.admin_mv_kb(code)); return

    # ════ KINO QO'SHISH ════
    if state == "add_sid":
        extra["series_id"] = txt.upper()
        db.set_state(msg.from_user.id, "add_total", extra)
        await msg.answer("Jami qismlar soni:", reply_markup=kb.admin_cancel_kb()); return

    if state == "add_total":
        try: extra["total_parts"] = int(txt)
        except: await msg.answer("❌ Faqat raqam!", reply_markup=kb.admin_cancel_kb()); return
        db.set_state(msg.from_user.id, "add_partnum", extra)
        await msg.answer(f"Bu qism nechchi? (1–{int(txt)}):", reply_markup=kb.admin_cancel_kb()); return

    if state == "add_partnum":
        try: extra["part"] = int(txt)
        except: await msg.answer("❌ Faqat raqam!", reply_markup=kb.admin_cancel_kb()); return
        db.set_state(msg.from_user.id, "add_code", extra)
        await msg.answer("🔑 Kino kodini kiriting:", reply_markup=kb.admin_cancel_kb()); return

    if state == "add_code":
        code = txt.upper()
        if db.get_movie(code):
            await msg.answer(f"⚠️ <code>{code}</code> allaqachon bor!",
                             reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return
        extra["code"] = code
        db.set_state(msg.from_user.id, "add_title", extra)
        await msg.answer(f"✅ Kod: <code>{code}</code>\n\n📝 Kino nomini kiriting:",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_title":
        extra["title"] = txt; db.set_state(msg.from_user.id, "add_year", extra)
        await msg.answer("📅 Yilini kiriting (yoki <code>-</code>):",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_year":
        extra["year"] = "" if txt=="-" else txt
        db.set_state(msg.from_user.id, "add_cat", extra)
        await msg.answer("🎭 Janrni kiriting:", reply_markup=kb.admin_cancel_kb()); return

    if state == "add_cat":
        extra["category"] = "" if txt=="-" else txt
        db.set_state(msg.from_user.id, "add_lang", extra)
        await msg.answer("🌐 Tilni kiriting (yoki <code>-</code>):",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_lang":
        extra["lang"] = "" if txt=="-" else txt
        db.set_state(msg.from_user.id, "add_dur", extra)
        await msg.answer("⏱ Davomiylik (yoki <code>-</code>):",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_dur":
        extra["duration"] = "" if txt=="-" else txt
        db.set_state(msg.from_user.id, "add_desc", extra)
        await msg.answer("📖 Tavsif kiriting (yoki <code>-</code>):",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_desc":
        extra["description"] = "" if txt=="-" else txt
        db.set_state(msg.from_user.id, "add_poster", extra)
        await msg.answer("🖼 Poster rasmini yuboring (yoki <code>-</code>):",
                         reply_markup=kb.admin_cancel_kb(), parse_mode=HTML); return

    if state == "add_poster":
        extra["poster_id"] = msg.photo[-1].file_id if msg.photo else ""
        db.set_state(msg.from_user.id, "add_video", extra)
        await msg.answer("🎞 Videoni yuboring — bot kanalga o'zi yuklaydi:",
                         reply_markup=kb.admin_cancel_kb()); return

    if state == "add_video":
        if not (msg.video or msg.document):
            await msg.answer("❌ Video yuboring!", reply_markup=kb.admin_cancel_kb()); return
        db.clear_state(msg.from_user.id)
        code = extra["code"]; title = extra.get("title","")
        part = extra.get("part",1); total = extra.get("total_parts",1)
        part_info = f" ({part}/{total}-qism)" if total>1 else ""
        w = await msg.answer(f"⏳ Kanalga yuklanmoqda...\n🎬 {title}\n🔑 {code}")
        cap = (f"🎬 <b>{title}{part_info}</b>\n"
               f"📅 {extra.get('year','—')} | 🎭 {extra.get('category','—')}\n"
               f"🔑 Kod: <code>{code}</code>")
        fid = await upload(bot, msg, cap)
        if not fid:
            await w.edit_text("❌ Kanalga yuklashda xatolik!\nSTORAGE_CHANNEL tekshiring."); return
        movie_data = {
            "title": title, "file_id": fid,
            "category": extra.get("category",""), "description": extra.get("description",""),
            "year": extra.get("year",""), "lang": extra.get("lang",""),
            "duration": extra.get("duration",""), "part": part, "total_parts": total,
            "series_id": extra.get("series_id",""), "poster_id": extra.get("poster_id",""),
        }
        db.add_movie(code, movie_data)
        await w.edit_text(
            f"✅ <b>Kino qo'shildi!</b>\n\n"
            f"🎬 <b>Nomi:</b> {title}{part_info}\n"
            f"🆔 <b>Kodi:</b> {code}\n"
            f"📅 <b>Yili:</b> {extra.get('year') or '—'}\n"
            f"🎭 <b>Janri:</b> {extra.get('category') or '—'}\n"
            f"🌍 <b>Tili:</b> {extra.get('lang') or '—'}\n"
            f"⏱ <b>Vaqti:</b> {extra.get('duration') or '—'}\n"
            f"👁 <b>Ko'rishlar:</b> 0\n\n"
            f"📝 <b>Tavsif:</b> {extra.get('description') or 'Yo\'q'}\n\n"
            f"💾 Kanalga yuklandi!",
            reply_markup=kb.admin_main_kb(), parse_mode=HTML
        )
