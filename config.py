import os

BOT_TOKEN       = os.getenv("BOT_TOKEN", "")
ADMIN_IDS       = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
STORAGE_CHANNEL = os.getenv("STORAGE_CHANNEL", "")
RENDER_URL      = os.getenv("RENDER_URL", "")
