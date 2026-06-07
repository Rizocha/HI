import os

BOT_TOKEN        = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS        = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]
RENDER_URL       = os.getenv("RENDER_URL", "")

# Kinolar saqlanadigan kanal ID (bot shu kanalga yuklaydi, file_id oladi)
# Misol: -1001234567890  yoki  @mening_storage_kanalim
# MUHIM: Bot bu kanalda ADMIN bo'lishi va xabar yuborish huquqi bo'lishi shart!
STORAGE_CHANNEL  = os.getenv("STORAGE_CHANNEL", "")

BOT_NAME     = "🎬 CineBot Pro"
BOT_VERSION  = "2.0"
