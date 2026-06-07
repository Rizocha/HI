import json, os
from datetime import datetime

DB = "data.json"

# ── init ──────────────────────────────────────────────────────────────────────
def _load():
    if not os.path.exists(DB):
        _save(_blank())
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return _blank()

def _blank():
    return {
        "movies": {},
        "channels": [],
        "users": {},          # user_id → {name, joined, favorites:[], history:[]}
        "stats": {"requests": 0},
        "states": {}
    }

def _save(d):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── USERS ─────────────────────────────────────────────────────────────────────
def ensure_user(user_id, full_name=""):
    d = _load()
    uid = str(user_id)
    if uid not in d["users"]:
        d["users"][uid] = {
            "id": user_id,
            "name": full_name,
            "joined": datetime.now().strftime("%d.%m.%Y"),
            "favorites": [],
            "history": [],
            "requests": 0
        }
        _save(d)

def get_user(user_id):
    return _load()["users"].get(str(user_id), {})

def get_all_users(limit=None):
    d = _load()
    users = list(d["users"].values())
    return users[:limit] if limit else users

def users_count():
    return len(_load()["users"])

# ── FAVORITES ─────────────────────────────────────────────────────────────────
def toggle_favorite(user_id, code):
    d = _load()
    uid = str(user_id)
    if uid not in d["users"]:
        return False
    favs = d["users"][uid].get("favorites", [])
    if code in favs:
        favs.remove(code)
        added = False
    else:
        favs.insert(0, code)
        if len(favs) > 50:
            favs = favs[:50]
        added = True
    d["users"][uid]["favorites"] = favs
    _save(d)
    return added

def get_favorites(user_id):
    u = get_user(user_id)
    codes = u.get("favorites", [])
    movies = []
    for c in codes:
        m = get_movie(c)
        if m:
            movies.append(m)
    return movies

# ── HISTORY ───────────────────────────────────────────────────────────────────
def add_history(user_id, code):
    d = _load()
    uid = str(user_id)
    if uid not in d["users"]:
        return
    hist = d["users"][uid].get("history", [])
    if code in hist:
        hist.remove(code)
    hist.insert(0, code)
    d["users"][uid]["history"] = hist[:20]
    d["users"][uid]["requests"] = d["users"][uid].get("requests", 0) + 1
    _save(d)

def get_history(user_id):
    u = get_user(user_id)
    codes = u.get("history", [])
    movies = []
    for c in codes[:10]:
        m = get_movie(c)
        if m:
            movies.append(m)
    return movies

# ── MOVIES ────────────────────────────────────────────────────────────────────
def add_movie(code, data: dict):
    d = _load()
    existing = d["movies"].get(code, {})
    data["code"] = code
    data.setdefault("views", existing.get("views", 0))
    data.setdefault("rating_sum", existing.get("rating_sum", 0))
    data.setdefault("rating_count", existing.get("rating_count", 0))
    data["added_at"] = existing.get("added_at", datetime.now().strftime("%d.%m.%Y"))
    d["movies"][code] = data
    _save(d)

def get_movie(code):
    return _load()["movies"].get(str(code).strip().upper())

def get_all_movies():
    return list(_load()["movies"].values())

def delete_movie(code):
    d = _load()
    if code in d["movies"]:
        del d["movies"][code]
        _save(d)
        return True
    return False

def update_views(code):
    d = _load()
    if code in d["movies"]:
        d["movies"][code]["views"] = d["movies"][code].get("views", 0) + 1
        d["stats"]["requests"] = d["stats"].get("requests", 0) + 1
        _save(d)

def add_rating(code, stars: int):
    d = _load()
    if code in d["movies"]:
        d["movies"][code]["rating_sum"] = d["movies"][code].get("rating_sum", 0) + stars
        d["movies"][code]["rating_count"] = d["movies"][code].get("rating_count", 0) + 1
        _save(d)

def get_avg_rating(movie: dict):
    rs = movie.get("rating_sum", 0)
    rc = movie.get("rating_count", 0)
    if rc == 0:
        return 0.0
    return round(rs / rc, 1)

def movies_count():
    return len(_load()["movies"])

# ── SEARCH ────────────────────────────────────────────────────────────────────
def search_movies(q: str):
    q = q.strip().lower()
    results = []
    for m in get_all_movies():
        score = 0
        if q == m.get("code", "").lower():
            score = 100
        elif q in m.get("title", "").lower():
            score = 50 + (10 if m["title"].lower().startswith(q) else 0)
        elif q in m.get("category", "").lower():
            score = 20
        elif q in m.get("description", "").lower():
            score = 5
        if score:
            results.append((score, m))
    results.sort(key=lambda x: (-x[0], -x[1].get("views", 0)))
    return [r[1] for r in results]

def get_top_movies(n=10):
    return sorted(get_all_movies(), key=lambda x: x.get("views", 0), reverse=True)[:n]

def get_by_category(cat):
    return [m for m in get_all_movies() if m.get("category", "") == cat]

def get_categories():
    return sorted(set(m.get("category", "") for m in get_all_movies() if m.get("category")))

def get_series_parts(series_id):
    return sorted(
        [m for m in get_all_movies() if m.get("series_id") == series_id],
        key=lambda x: x.get("part", 1)
    )

def get_similar(movie: dict, limit=5):
    cat = movie.get("category", "")
    code = movie.get("code", "")
    candidates = [m for m in get_all_movies()
                  if m.get("category") == cat and m.get("code") != code]
    return sorted(candidates, key=lambda x: x.get("views", 0), reverse=True)[:limit]

# ── CHANNELS ──────────────────────────────────────────────────────────────────
def get_channels():
    return _load().get("channels", [])

def add_channel(ch_id, username, name):
    d = _load()
    if any(c["id"] == ch_id for c in d["channels"]):
        return False
    d["channels"].append({"id": ch_id, "username": username, "name": name})
    _save(d)
    return True

def remove_channel(ch_id):
    d = _load()
    before = len(d["channels"])
    d["channels"] = [c for c in d["channels"] if c["id"] != ch_id]
    if len(d["channels"]) < before:
        _save(d)
        return True
    return False

# ── STATS ─────────────────────────────────────────────────────────────────────
def get_stats():
    d = _load()
    movies = list(d["movies"].values())
    return {
        "users": len(d["users"]),
        "movies": len(movies),
        "requests": d["stats"].get("requests", 0),
        "channels": len(d["channels"]),
        "top": sorted(movies, key=lambda x: x.get("views", 0), reverse=True)[:5],
        "categories": len(get_categories()),
    }

# ── STATE MACHINE ─────────────────────────────────────────────────────────────
def set_state(uid, state, extra=None):
    d = _load()
    d["states"][str(uid)] = {"s": state, "e": extra or {}}
    _save(d)

def get_state(uid):
    return _load()["states"].get(str(uid), {"s": None, "e": {}})

def clear_state(uid):
    d = _load()
    d["states"].pop(str(uid), None)
    _save(d)
