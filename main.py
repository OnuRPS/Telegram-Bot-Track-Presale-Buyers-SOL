import os
import asyncio
import aiohttp
import json
from telegram import Bot
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = "https://pandabao.org/wp-content/uploads/2025/05/pandaBao-1200-x-630-px-1200-x-630-px.gif"
SOLANA_RPC = "https://rpc.helius.xyz/?api-key=4db5289f-5c8e-4e55-8478-dd1e73ee2eee"
RAY_MINT = "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"
RAY_PROGRAM_ID = "RVKd61ztZW9GdGz5oYX1JcNBJbYtD7Nm9ujap7hKbTg"  # Radium V5 Program
WSOL_MINT = "So11111111111111111111111111111111111111112"

bot = Bot(token=TELEGRAM_TOKEN)
last_sig = None

async def get_ray_info():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=raydium&vs_currencies=usd&include_market_cap=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
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

async def monitor_radium_buys():
    global last_sig
    client = AsyncClient(SOLANA_RPC)
    print("🟢 Monitoring WSOL → RAY buys via Radium V5...")

    while True:
        try:
            sigs = await client.get_signatures_for_address(Pubkey.from_string(RAY_PROGRAM_ID), limit=5)
            for sig_info in sigs.value:
                sig = sig_info.signature
                if sig == last_sig:
                    continue
                tx = await client.get_transaction(sig, encoding="jsonParsed")
                tx_json = json.loads(tx.value.to_json())
                instructions = tx_json["transaction"]["message"].get("instructions", [])
                meta = tx_json.get("meta", {})
                post_balances = meta.get("postTokenBalances", [])
                pre_balances = meta.get("preTokenBalances", [])

                found_buy = False
                amount_sol = 0.0
                sender = sig_info.pubkey or "Unknown"

                for balance in post_balances:
                    if balance.get("mint") == RAY_MINT:
                        idx = balance.get("accountIndex")
                        pre_amt = next((x for x in pre_balances if x.get("accountIndex") == idx), {})
                        old = float(pre_amt.get("uiTokenAmount", {}).get("uiAmount", 0))
                        new = float(balance.get("uiTokenAmount", {}).get("uiAmount", 0))
                        if new > old:
                            found_buy = True
                            amount_sol = new - old  # not perfect, just indication
                            break

                if found_buy and amount_sol > 0:
                    price, market_cap = await get_ray_info()
                    supply = "554,998,949.95"
                    holders = "239,142"
                    await send_telegram_message(sender, amount_sol, price, market_cap, supply, holders)
                    last_sig = sig
        except Exception as e:
            print(f"❌ Error: {e}")
        await asyncio.sleep(10)

async def main():
    await monitor_radium_buys()

if __name__ == "__main__":
    asyncio.run(main())
