import os
import asyncio
import aiohttp
from telegram import Bot

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
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

async def send_telegram_message(sender, recipient, amount_sol, price, market_cap, supply, holders):
    approx_usd = round(amount_sol * price, 2)
    message = (
        f"\ud83d\ude80 New $RAY contribution detected!\n\n"
        f"\ud83d\udd01 From: {sender}\n"
        f"\ud83d\udce5 To: {recipient}\n"
        f"\ud83d\udfe8 Amount Received:\n"
        f"\u250c────────────────────────────────────────┐\n"
        f"│  {amount_sol:.4f} SOL (~${approx_usd})  │\n"
        f"└────────────────────────────────────────┘\n\n"
        f"💵 Price: ${price}\n"
        f"📈 Market Cap: ${market_cap:,.2f}\n"
        f"💰 Current Supply: {supply}\n"
        f"📣 Holders: {holders}\n"
        f"🌐 Website: raydium.io\n\n"
        f"───────────────────\n"
        f"🤖 *BuyDetector™ Solana*\n"
        f"🔧 by [ReactLAB](https://t.me/PandaBaoOfficial)"
    )

    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# === MAIN ===
async def main():
    sender = "Unknown"
    recipient = "VaultWalletTest"
    amount_sol = 0.0600

    price, market_cap = await get_ray_info()
    supply = "554,998,949.95"
    holders = "239,140"

    await send_telegram_message(sender, recipient, amount_sol, price, market_cap, supply, holders)

if __name__ == "__main__":
    asyncio.run(main())
