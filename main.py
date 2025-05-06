import os, asyncio, aiohttp, json
from telegram import Bot
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

# === CONFIG ===
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
MONITORED_WALLET = "D6FDaJjvRwBSm54rBP7ViRbF7KQxzpNw35TFWNWwpsbB"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = os.getenv("GIF_URL")
WSOL_MINT = "So11111111111111111111111111111111111111112"

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
    return '🥇' * min(bullets_count, 100)

async def test_telegram_message():
    print("🧪 Sending test message to Telegram...")
    text = (
        "✅ Bot started and connected successfully!\n\n"
        "🟢 Solana BuyDetector™ is live.\n"
        "🔍 Waiting for first transaction..."
    )
    try:
        if GIF_URL:
            await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=text, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        print("✅ Test message sent to Telegram!")
    except Exception as e:
        print(f"❌ Failed to send test Telegram message: {e}")

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
                if not tx_resp.value:
                    await asyncio.sleep(10)
                    continue

                try:
                    raw = tx_resp.value.to_json()
                    parsed = json.loads(raw) if isinstance(raw, str) else raw
                except Exception as e:
                    print(f"⚠️ Failed to convert transaction to JSON: {e}")
                    await asyncio.sleep(10)
                    continue

                tx = parsed.get("transaction", {})
                msg = tx.get("message", {})
                instructions = msg.get("instructions", [])

                for i, instr in enumerate(instructions):
                    if not isinstance(instr, dict):
                        print(f"⚠️ Ignored non-dict instruction at index {i}")
                        continue

                    parsed_data = instr.get("parsed")

                    sol_amount = 0
                    from_addr = ""
                    to_addr = ""

                    if parsed_data and isinstance(parsed_data, dict):
                        if instr["program"] == "system" and parsed_data.get("type") == "transfer":
                            info = parsed_data.get("info", {})
                            lamports = int(info.get("lamports", 0))
                            sol_amount = lamports / 1e9
                            from_addr = info.get("source", "")
                            to_addr = info.get("destination", "")

                        elif instr["program"] == "spl-token" and parsed_data.get("type") == "transfer":
                            info = parsed_data.get("info", {})
                            if (
                                info.get("mint") == WSOL_MINT and
                                info.get("destination") == MONITORED_WALLET
                            ):
                                amount = int(info.get("amount", 0))
                                sol_amount = amount / 1e9
                                from_addr = info.get("source", "")
                                to_addr = info.get("destination", "")
                    else:
                        print(f"⚠️ Skipping unparsed instruction at index {i}")
                        continue

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
                                await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg_text, parse_mode="Markdown")
                            else:
                                await bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown")
                            print(f"✅ TX posted: {sig}")
                        except Exception as e:
                            print(f"❌ Failed to send Telegram message: {e}")

        except Exception as e:
            print(f"⚠️ Outer error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(test_telegram_message())
    asyncio.run(check_transactions())
