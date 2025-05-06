from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
import asyncio, os, aiohttp
from telegram import Bot

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
MONITORED_WALLET = "FsG7BTpThCsnP2c78qc9F2inYEqUoSEKGCAQ8eMyYtsi"  # Replace with your actual wallet
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = os.getenv("GIF_URL")

bot = Bot(token=TELEGRAM_TOKEN)

last_sig = None

async def get_sol_price():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd") as r:
                data = await r.json()
                return float(data["solana"]["usd"])
    except:
        return 0.0

def generate_bullets(sol_amount):
    bullets_count = int(sol_amount / 0.1)
    bullets_count = min(bullets_count, 100)
    return '🥇' * bullets_count

async def check_transactions():
    global last_sig
    client = AsyncClient(SOLANA_RPC)
    pubkey = Pubkey.from_string(MONITORED_WALLET)
    print("🟢 Solana BuyDetector™ activated.")

    while True:
        try:
            sigs_resp = await client.get_signatures_for_address(pubkey, limit=1)
            sig_info = sigs_resp.value[0]
            sig = sig_info.signature

            if sig != last_sig:
                last_sig = sig
                tx_resp = await client.get_transaction(sig, encoding="jsonParsed", max_supported_transaction_version=0)
                parsed = tx_resp.value

                for instr in parsed['transaction']['message']['instructions']:
                    if instr['program'] == 'system':
                        lamports = int(instr['parsed']['info']['lamports'])
                        sol_amount = lamports / 1e9
                        from_addr = instr['parsed']['info']['source']
                        to_addr = instr['parsed']['info']['destination']

                        sol_price = await get_sol_price()
                        usd_value = sol_amount * sol_price
                        bullets = generate_bullets(sol_amount)

                        msg = (
                            f"🪙 *New $BabyGOV transaction detected (Solana)*\n\n"
                            f"🔁 From: `{from_addr}`\n"
                            f"📥 To: `{to_addr}`\n"
                            f"🟨 *Amount Purchased:*\n"
                            f"┌────────────────────────────┐\n"
                            f"│  {sol_amount:.4f} SOL (~${usd_value:,.2f})  │\n"
                            f"└────────────────────────────┘\n"
                            f"{bullets}\n\n"
                            f"🔗 [View on Solscan](https://solscan.io/tx/{sig})\n\n"
                            f"───────────────\n"
                            f"🤖 𝓑𝓾𝔂𝓓𝓮𝓽𝓮𝓬𝓽𝓸𝓻™ Solana\n"
                            f"🔧 by ReactLAB"
                        )

                        if GIF_URL:
                            await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg, parse_mode="Markdown")
                        else:
                            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                        print(f"✅ TX posted: {sig}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(check_transactions())
