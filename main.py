import os, asyncio, aiohttp, json
from telegram import Bot
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
MONITORED_WALLET = "FsG7BTpThCsnP2c78qc9F2inYEqUoSEKGCAQ8eMyYtsi"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = os.getenv("GIF_URL")

bot = Bot(token=TELEGRAM_TOKEN)
last_sig = None
WSOL_MINT = "So11111111111111111111111111111111111111112"

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

async def test_telegram_message():
    print("🧪 Sending test message to Telegram...")
    test_text = (
        "✅ Bot started and connected successfully!\n\n"
        "🟢 Solana BuyDetector is live.\n"
        "🔍 Waiting for first transaction..."
    )
    try:
        if GIF_URL:
            bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=test_text)
        else:
            bot.send_message(chat_id=CHAT_ID, text=test_text)
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
                    print(f"⚠️ Transaction data missing for {sig}")
                    await asyncio.sleep(10)
                    continue

                val = tx_resp.value

                try:
                    if hasattr(val, "to_json"):
                        parsed = val.to_json()
                    elif isinstance(val, dict):
                        parsed = val
                    elif isinstance(val, str) and val.startswith("{") and "transaction" in val:
                        parsed = json.loads(val)
                    else:
                        print(f"⚠️ Skipping unexpected tx format: {val}")
                        await asyncio.sleep(10)
                        continue
                except Exception as e:
                    print(f"⚠️ Failed to parse transaction: {e}")
                    await asyncio.sleep(10)
                    continue

                tx = parsed.get("transaction")
                if not isinstance(tx, dict):
                    print(f"⚠️ Skipping malformed transaction (not dict): {type(tx)}")
                    await asyncio.sleep(10)
                    continue

                msg = tx.get("message", {})
                instructions = msg.get("instructions", [])

                for i, instr in enumerate(instructions):
                    if not isinstance(instr, dict):
                        print(f"⚠️ Ignored non-dict instruction at index {i}")
                        continue

                    try:
                        parsed_data = instr.get("parsed")
                        if not isinstance(parsed_data, dict):
                            print(f"⚠️ Skipping unparsed instruction at index {i}")
                            continue

                        sol_amount = 0
                        from_addr = ""
                        to_addr = ""

                        if instr["program"] == "system" and parsed_data.get("type") == "transfer":
                            info = parsed_data.get("info", {})
                            lamports = int(info.get("lamports", 0))
                            sol_amount = lamports / 1e9
                            from_addr = info.get("source", "")
                            to_addr = info.get("destination", "")

                        elif instr["program"] == "spl-token" and parsed_data.get("type") == "transfer":
                            info = parsed_data.get("info", {})
                            token_dest = info.get("destination", "")
                            token_mint = info.get("mint", "")
                            if token_dest == MONITORED_WALLET and token_mint == WSOL_MINT:
                                sol_amount = int(info.get("amount", 0)) / 1e9
                                from_addr = info.get("source", "")
                                to_addr = token_dest

                        if sol_amount > 0:
                            sol_price = await get_sol_price()
                            usd_value = sol_amount * sol_price
                            bullets = generate_bullets(sol_amount)

                            msg_text = (
                                f"🪙 New $BabyGOV contribution detected!\n\n"
                                f"🔁 From: `{from_addr}`\n"
                                f"📥 To: `{to_addr}`\n"
                                f"🟨 Amount:\n"
                                f"┌────────────────────────────┐\n"
                                f"│  {sol_amount:.4f} SOL (~${usd_value:,.2f})  │\n"
                                f"└────────────────────────────┘\n"
                                f"{bullets}\n\n"
                                f"🔗 https://solscan.io/tx/{sig}\n\n"
                                f"───────────────\n"
                                f"🤖 BuyDetector™ Solana\n"
                                f"🔧 by ReactLAB"
                            )

                            if GIF_URL:
                                bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg_text, parse_mode="Markdown")
                            else:
                                bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown")

                            print(f"✅ TX posted: {sig}")

                    except Exception as inner_e:
                        print(f"⚠️ Error inside instruction at index {i}: {inner_e}")

        except Exception as e:
            print(f"⚠️ Outer error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(test_telegram_message())
    asyncio.run(check_transactions())
