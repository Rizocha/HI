import json, os
from datetime import datetime

DB = "data.json"

def _load():
    if not os.path.exists(DB):
        _save(_blank())
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        d = _blank(); _save(d); return d

def _blank():
    return {
        "movies": {},
        "channels": [],      # Telegram majburiy obuna kanallari
        "ext_channels": [],  # Instagram va boshqa tashqi havolalar
        "users": {},
        "texts": {
            "start":     "Salom {name}!\n\nKino kodini yuboring — video darhol keladi.\n\nMisol: 1  2  3",
            "not_found": "Kino topilmadi. Kodni tekshiring.",
            "sub_req":   "Kinoni olish uchun quyidagi kanallarga obuna buling!",
            "sub_ok":    "Obuna tasdiqlandi! Endi kino kodini yuboring.",
            "no_movies": "Hozircha kinolar yuq.",
        },
        "stats": {"requests": 0},
        "monitoring": [],    # har bir so'rov logi
        "states": {}
    }

def _save(d):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── TEXTS ─────────────────────────────────────────────────────────────────────
def get_text(key, **kwargs):
    d = _load()
    t = d.get("texts", {}).get(key, key)
    try: return t.format(**kwargs)
    except: return t

def set_text(key, value):
    d = _load()
    if "texts" not in d: d["texts"] = {}
    d["texts"][key] = value; _save(d)

def get_all_texts():
    return _load().get("texts", {})

# ── USERS ─────────────────────────────────────────────────────────────────────
def ensure_user(uid, name=""):
    d = _load(); k = str(uid)
    if k not in d["users"]:
        d["users"][k] = {
            "id": uid, "name": name,
            "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "favorites": [], "history": [], "requests": 0
        }
        _save(d)

def get_user(uid):
    return _load()["users"].get(str(uid), {})

def all_users():
    return list(_load()["users"].values())

def users_count():
    return len(_load()["users"])

# ── FAVORITES ─────────────────────────────────────────────────────────────────
def toggle_fav(uid, code):
    d = _load(); k = str(uid)
    if k not in d["users"]: return False
    favs = d["users"][k].get("favorites", [])
    if code in favs: favs.remove(code); added = False
    else: favs.insert(0, code); favs = favs[:50]; added = True
    d["users"][k]["favorites"] = favs; _save(d); return added

def get_favs(uid):
    return [m for c in get_user(uid).get("favorites", []) if (m := get_movie(c))]

# ── HISTORY ───────────────────────────────────────────────────────────────────
def add_history(uid, code):
    d = _load(); k = str(uid)
    if k not in d["users"]: return
    h = d["users"][k].get("history", [])
    if code in h: h.remove(code)
    h.insert(0, code); d["users"][k]["history"] = h[:20]
    d["users"][k]["requests"] = d["users"][k].get("requests", 0) + 1
    d["stats"]["requests"] = d["stats"].get("requests", 0) + 1
    _save(d)

def get_history(uid):
    return [m for c in get_user(uid).get("history", [])[:10] if (m := get_movie(c))]

# ── MONITORING ────────────────────────────────────────────────────────────────
def log_visit(uid, action, code=""):
    """Har bir tashrif/harakat loglanadi."""
    d = _load()
    now = datetime.now()
    entry = {
        "uid":    uid,
        "action": action,       # "watch", "start", "search", "list"
        "code":   code,
        "date":   now.strftime("%d.%m.%Y"),
        "hour":   now.hour,
        "time":   now.strftime("%H:%M"),
    }
    logs = d.get("monitoring", [])
    logs.append(entry)
    # Oxirgi 5000 ta log saqlanadi
    d["monitoring"] = logs[-5000:]
    _save(d)

def get_monitoring_summary():
    """Monitoring hisoboti."""
    d = _load()
    logs = d.get("monitoring", [])
    if not logs:
        return None

    now = datetime.now()
    today = now.strftime("%d.%m.%Y")
    yesterday = (now.replace(day=now.day-1) if now.day > 1 else now).strftime("%d.%m.%Y")

    today_logs     = [l for l in logs if l.get("date") == today]
    yesterday_logs = [l for l in logs if l.get("date") == yesterday]

    # Soatlar bo'yicha bugun
    hours = {}
    for l in today_logs:
        h = l.get("hour", 0)
        hours[h] = hours.get(h, 0) + 1

    # Eng faol soat
    peak_hour = max(hours, key=hours.get) if hours else None

    # Haftalik
    week_logs = logs[-1000:]
    dates = {}
    for l in week_logs:
        dt = l.get("date","")
        dates[dt] = dates.get(dt, 0) + 1

    # Unikal foydalanuvchilar bugun
    today_users = len(set(l.get("uid") for l in today_logs))

    return {
        "total_logs":     len(logs),
        "today":          len(today_logs),
        "today_users":    today_users,
        "yesterday":      len(yesterday_logs),
        "peak_hour":      peak_hour,
        "peak_count":     hours.get(peak_hour, 0) if peak_hour is not None else 0,
        "hours":          hours,
        "recent_dates":   sorted(dates.items(), reverse=True)[:7],
    }

def get_hourly_chart():
    """24 soat bo'yicha so'rovlar (bugun)."""
    d = _load()
    today = datetime.now().strftime("%d.%m.%Y")
    logs = [l for l in d.get("monitoring", []) if l.get("date") == today]
    hours = {i: 0 for i in range(24)}
    for l in logs:
        h = l.get("hour", 0)
        hours[h] = hours.get(h, 0) + 1
    return hours

# ── MOVIES ────────────────────────────────────────────────────────────────────
def add_movie(code, data: dict):
    d = _load()
    ex = d["movies"].get(code, {})
    data["code"] = code
    data.setdefault("views", ex.get("views", 0))
    data.setdefault("viewers", ex.get("viewers", []))
    data["added_at"] = ex.get("added_at", datetime.now().strftime("%d.%m.%Y"))
    d["movies"][code] = data; _save(d)

def get_movie(code):
    if not code: return None
    return _load()["movies"].get(str(code).strip().upper())

def all_movies():
    return list(_load()["movies"].values())

def delete_movie(code):
    d = _load()
    if code in d["movies"]: del d["movies"][code]; _save(d); return True
    return False

def inc_views(code, uid=None):
    d = _load()
    if code not in d["movies"]: return
    d["movies"][code]["views"] = d["movies"][code].get("views", 0) + 1
    if uid:
        viewers = d["movies"][code].get("viewers", [])
        if uid not in viewers:
            viewers.append(uid)
            d["movies"][code]["viewers"] = viewers
    _save(d)

def movies_count():
    return len(_load()["movies"])

def auto_rating(m: dict) -> float:
    v = m.get("views", 0)
    if v >= 1000: return 5.0
    if v >= 200:  return 4.0
    if v >= 50:   return 3.0
    if v >= 10:   return 2.0
    return 1.0 if v > 0 else 0.0

def star_str(rating: float) -> str:
    if not rating: return "—"
    return "⭐" * int(round(rating))

def avg_rating(m: dict) -> float:
    return auto_rating(m)

# ── SEARCH ────────────────────────────────────────────────────────────────────
def search(q: str):
    q = q.strip().lower()
    res = []
    for m in all_movies():
        sc = 0
        if q == m.get("code","").lower(): sc = 100
        elif q in m.get("title","").lower(): sc = 50 + (20 if m["title"].lower().startswith(q) else 0)
        elif q in m.get("category","").lower(): sc = 20
        elif q in m.get("description","").lower(): sc = 5
        if sc: res.append((sc, m))
    res.sort(key=lambda x: (-x[0], -x[1].get("views", 0)))
    return [r[1] for r in res]

def top_movies(n=10):
    return sorted(all_movies(), key=lambda x: x.get("views", 0), reverse=True)[:n]

def by_category(cat):
    return [m for m in all_movies() if m.get("category") == cat]

def categories():
    return sorted(set(m.get("category","") for m in all_movies() if m.get("category")))

def series_parts(sid):
    return sorted([m for m in all_movies() if m.get("series_id") == sid], key=lambda x: x.get("part",1))

# ── TELEGRAM CHANNELS (majburiy obuna) ───────────────────────────────────────
def get_channels():
    return _load().get("channels", [])

def add_channel(cid, username, name):
    d = _load()
    if any(c["id"] == cid for c in d["channels"]): return False
    d["channels"].append({"id": cid, "username": username, "name": name})
    _save(d); return True

def remove_channel(cid):
    d = _load(); before = len(d["channels"])
    d["channels"] = [c for c in d["channels"] if c["id"] != cid]
    if len(d["channels"]) < before: _save(d); return True
    return False

# ── TASHQI HAVOLALAR (Instagram, YouTube, website) ───────────────────────────
def get_ext_channels():
    return _load().get("ext_channels", [])

def add_ext_channel(name, url, icon="🔗"):
    d = _load()
    if "ext_channels" not in d: d["ext_channels"] = []
    # Mavjudmi?
    if any(c["url"] == url for c in d["ext_channels"]): return False
    d["ext_channels"].append({"name": name, "url": url, "icon": icon})
    _save(d); return True

def remove_ext_channel(url):
    d = _load()
    before = len(d.get("ext_channels", []))
    d["ext_channels"] = [c for c in d.get("ext_channels", []) if c["url"] != url]
    if len(d["ext_channels"]) < before: _save(d); return True
    return False

# ── STATS ─────────────────────────────────────────────────────────────────────
def stats():
    d = _load()
    mvs = list(d["movies"].values())
    mon = get_monitoring_summary()
    return {
        "users":    len(d["users"]),
        "movies":   len(mvs),
        "requests": d["stats"].get("requests", 0),
        "channels": len(d["channels"]),
        "ext_ch":   len(d.get("ext_channels", [])),
        "top5":     sorted(mvs, key=lambda x: x.get("views",0), reverse=True)[:5],
        "today":    mon["today"] if mon else 0,
        "today_users": mon["today_users"] if mon else 0,
        "peak_hour":   mon["peak_hour"] if mon else None,
        "peak_count":  mon["peak_count"] if mon else 0,
    }

# ── STATES ────────────────────────────────────────────────────────────────────
def set_state(uid, state, extra=None):
    d = _load(); d["states"][str(uid)] = {"s": state, "e": extra or {}}; _save(d)

def get_state(uid):
    return _load()["states"].get(str(uid), {"s": None, "e": {}})

def clear_state(uid):
    d = _load(); d["states"].pop(str(uid), None); _save(d)
