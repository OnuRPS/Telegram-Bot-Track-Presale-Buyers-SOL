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

def debug(msg):
    print(f"[DEBUG] {msg}")

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
    global last_sig
    client = AsyncClient(SOLANA_RPC)
    pubkey = Pubkey.from_string(MONITORED_WALLET)
    print("🟢 Solana BuyDetector™ activated.")

    while True:
        try:
            sigs_resp = await client.get_signatures_for_address(pubkey, limit=1)
            sig_info = sigs_resp.value[0]
            sig = sig_info.signature
            first_time = last_sig is None

            if sig != last_sig or first_time:
                tx_resp = await client.get_transaction(sig, encoding="jsonParsed", max_supported_transaction_version=0)
                if not tx_resp.value:
                    await asyncio.sleep(10)
                    continue

                parsed = tx_resp.value.transaction
                msg = parsed.get("message", {})
                instructions = msg.get("instructions", [])

                debug(f"TX {sig} has {len(instructions)} instruction(s)")

                for i, instr in enumerate(instructions):
                    sol_amount = 0
                    from_addr = ""
                    to_addr = ""

                    program = instr.get("program", "unknown")
                    parsed_data = instr.get("parsed")

                    debug(f"Instr #{i} program: {program}")
                    if parsed_data:
                        debug(f"Instr #{i} type: {parsed_data.get('type', 'n/a')} parsed")

                    # SYSTEM transfer (SOL)
                    if parsed_data and program == "system" and parsed_data.get("type") == "transfer":
                        info = parsed_data.get("info", {})
                        lamports = int(info.get("lamports", 0))
                        sol_amount = lamports / 1e9
                        from_addr = info.get("source", "")
                        to_addr = info.get("destination", "")
                        debug(f"Detected SOL transfer: {sol_amount} SOL")

                    # SPL transfer (WSOL mint) — detect manually
                    elif program == "spl-token":
                        info = parsed_data.get("info", {}) if parsed_data else {}
                        mint = info.get("mint", "")
                        dest = info.get("destination", "")

                        if mint == WSOL_MINT and dest == MONITORED_WALLET:
                            amount = int(info.get("amount", 0))
                            sol_amount = amount / 1e9
                            from_addr = info.get("source", "")
                            to_addr = dest
                            debug(f"Detected WSOL transfer: {sol_amount} SOL")
                        else:
                            debug(f"Instr #{i} is SPL-token but not WSOL to our wallet.")
                            continue
                    else:
                        debug(f"Instr #{i} skipped: not SOL/WSOL transfer")
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
                                bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg_text, parse_mode="Markdown")
                            else:
                                bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown")
                            print(f"✅ TX posted: {sig}")
                            last_sig = sig
                        except Exception as e:
                            print(f"❌ Failed to send Telegram message: {e}")

        except Exception as e:
            print(f"⚠️ Outer error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    test_telegram_message()
    asyncio.run(check_transactions())
