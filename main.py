import os
import asyncio
import aiohttp
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = "https://pandabao.org/wp-content/uploads/2025/05/pandaBao-1200-x-630-px-1200-x-630-px.gif"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=raydium&vs_currencies=usd&include_market_cap=true"
RAY_MINT = "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"

bot = Bot(token=TELEGRAM_TOKEN)

async def get_ray_info():
    async with aiohttp.ClientSession() as session:
        async with session.get(COINGECKO_API) as resp:
            data = await resp.json()
            price = data["raydium"]["usd"]
            market_cap = data["raydium"]["usd_market_cap"]
            return price, market_cap

async def send_telegram_message(sender, amount_sol, price, market_cap, supply, holders):
    approx_usd = round(amount_sol * price, 2)
    message = (
        f"\ud83d\ude80 *New $RAY buy detected!*\n\n"
        f"\ud83d\udd01 *From:* `{sender}`\n"
        f"\ud83d\udce5 *Amount:* {amount_sol:.4f} SOL (~${approx_usd})\n\n"
        f"\ud83d\udcb5 *Price:* ${price}\n"
        f"\ud83d\udcc8 *Market Cap:* ${market_cap:,.2f}\n"
        f"\ud83d\udcb0 *Current Supply:* {supply}\n"
        f"\ud83d\udce3 *Holders:* {holders}\n"
        f"\ud83c\udf10 Website: raydium.io\n\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\ud83e\udd16 *BuyDetector\u2122 Solana*\n"
        f"\ud83d\udd27 by [ReactLAB](https://t.me/PandaBaoOfficial)"
    )

    await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=message, parse_mode="Markdown")

# === MAIN ===
async def main():
    sender = "Unknown"
    amount_sol = 0.0600

    price, market_cap = await get_ray_info()
    supply = "554,998,949.95"
    holders = "239,142"

    await send_telegram_message(sender, amount_sol, price, market_cap, supply, holders)

if __name__ == "__main__":
    asyncio.run(main())
