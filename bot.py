import os
import asyncio
import aiohttp
import json
from telegram import Bot
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from dotenv import load_dotenv

load_dotenv()

SOLANA_RPC = "https://rpc.helius.xyz/?api-key=4db5289f-5c8e-4e55-8478-dd1e73ee2eee"
MONITORED_WALLET = "D6FDaJjvRwBSm54rBP7ViRbF7KQxzpNw35TFWNWwpsbB"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = os.getenv("GIF_URL")
WSOL_MINT = "So11111111111111111111111111111111111111112"

bot = Bot(token=TELEGRAM_TOKEN)
last_sig = None
initial_run = True

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
    return '🥇' * min(bullets_count, 100)

def test_telegram_message():
    print("🧪 Sending test message to Telegram...")
    text = (
        "✅ Bot started and connected successfully!\n\n"
        "🟢 Solana BuyDetector™ is live.\n"
        "🔍 Waiting for first transaction..."
    )
    try:
        if GIF_URL:
            bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Test message sent to Telegram!")
    except Exception as e:
        print(f"❌ Failed to send test Telegram message: {e}")

async def check_transactions():
    global last_sig, initial_run
    client = AsyncClient(SOLANA_RPC)
    pubkey = Pubkey.from_string(MONITORED_WALLET)
    print("🟢 Solana BuyDetector™ activated.")

    while True:
        try:
            sigs_resp = await client.get_signatures_for_address(pubkey, limit=1)
            sig_info = sigs_resp.value[0]
            sig = sig_info.signature

            if sig != last_sig or initial_run:
                initial_run = False
                print(f"🔍 Checking TX: {sig}")
                tx_resp = await client.get_transaction(sig, encoding="jsonParsed", max_supported_transaction_version=0)
                if not tx_resp.value:
                    await asyncio.sleep(10)
                    continue

                # Accesăm întregul JSON, nu doar tranzacția
                tx_json = json.loads(tx_resp.value.to_json())

                transaction = tx_json.get("transaction", {})
                msg = transaction.get("message", {})
                instructions = msg.get("instructions", [])
                accs = msg.get("accountKeys", [])
                meta = tx_json.get("meta", {})

                print(f"[DEBUG] instructions = {instructions}")
                print(f"[DEBUG] meta keys: {list(meta.keys())}")

                sol_amount = 0
                from_addr = "Unknown"
                to_addr = MONITORED_WALLET

                # 1️⃣ WSOL via postTokenBalances
                for b in meta.get("postTokenBalances", []):
                    if b.get("owner") == MONITORED_WALLET and b.get("mint") == WSOL_MINT:
                        sol_amount = float(b.get("uiTokenAmount", {}).get("uiAmount", 0))
                        print(f"✅ WSOL detected: {sol_amount} SOL")
                        break

                # 2️⃣ SOL direct via parsed instructions
                if sol_amount == 0:
                    for instr in instructions:
                        if instr.get("program") == "system":
                            parsed = instr.get("parsed", {})
                            if parsed.get("type") == "transfer":
                                info = parsed.get("info", {})
                                if info.get("destination") == MONITORED_WALLET:
                                    lamports = int(info.get("lamports", 0))
                                    sol_amount = lamports / 1e9
                                    from_addr = info.get("source", "Unknown")
                                    to_addr = info.get("destination", MONITORED_WALLET)
                                    print(f"✅ SOL detected: {sol_amount} SOL")
                                    break

                # 3️⃣ Fallback: balance delta
                if sol_amount == 0 and meta.get("preBalances") and meta.get("postBalances"):
                    try:
                        pre = meta["preBalances"]
                        post = meta["postBalances"]
                        for i, acc in enumerate(accs):
                            if isinstance(acc, dict):
                                pubkey = acc.get("pubkey")
                            else:
                                pubkey = acc
                            if pubkey == MONITORED_WALLET:
                                diff = int(post[i]) - int(pre[i])
                                if diff > 0:
                                    sol_amount = diff / 1e9
                                    print(f"⚠️ Fallback balance delta: {sol_amount} SOL")
                                    break
                    except Exception as e:
                        print(f"❌ Fallback balance check error: {e}")

                if sol_amount > 0:
                    sol_price = await get_sol_price()
                    usd_value = sol_amount * sol_price
                    bullets = generate_bullets(sol_amount)

                    msg_text = (
                        f"🪙 *New $BabyGOV contribution detected!*\n\n"
                        f"🔁 From: `{from_addr}`\n"
                        f"📥 To: `{to_addr}`\n"
                        f"🟨 *Amount:*\n"
                        f"┌────────────────────────────┐\n"
                        f"│  {sol_amount:.4f} SOL (~${usd_value:,.2f})  │\n"
                        f"└────────────────────────────┘\n"
                        f"{bullets}\n\n"
                        f"🔗 [View on Solscan](https://solscan.io/tx/{sig})\n\n"
                        f"───────────────\n"
                        f"🤖 𝓑𝓾𝔂𝓓𝓮𝓽𝓮𝓬𝓽𝓸𝓻™ Solana\n"
                        f"🔧 by ReactLAB"
                    )

                    try:
                        if GIF_URL:
                            bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg_text, parse_mode="Markdown")
                        else:
                            bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown")
                        print(f"📬 TX posted: {sig}")
                        last_sig = sig
                    except Exception as e:
                        print(f"❌ Failed to send Telegram message: {e}")
                else:
                    print("⚠️ No SOL or WSOL received in this transaction.")

        except Exception as e:
            print(f"⚠️ Outer error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    test_telegram_message()
    asyncio.run(check_transactions())
