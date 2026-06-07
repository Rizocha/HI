import asyncio, aiohttp, os, logging
from aiohttp import web

log = logging.getLogger(__name__)

async def health(r): return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info(f"Web server: port {port}")

async def self_ping():
    url = os.getenv("RENDER_URL", "")
    if not url: return
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=10)) as r:
                    log.info(f"Ping: {r.status}")
        except Exception as e:
            log.warning(f"Ping xato: {e}")
        await asyncio.sleep(13 * 60)
