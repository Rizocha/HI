import asyncio, aiohttp, os, logging
from aiohttp import web

async def health(r): return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()

async def self_ping():
    url = os.getenv("RENDER_URL", "")
    if not url: return
    await asyncio.sleep(60)
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                await s.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=10))
        except: pass
        await asyncio.sleep(13*60)
