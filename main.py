import os, asyncio, aiohttp
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GIF_URL = os.getenv("GIF_URL")
MONITORED_WALLET = "FsG7BTpThCsnP2c78qc9F2inYEqUoSEKGCAQ8eMyYtsi"

bot = Bot(token=TELEGRAM_TOKEN)

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
    try:
        print("🧪 Sending test message to Telegram...")
        test_text = "✅ *Bot started in SIMULATION MODE*\n\n🟢 Solana BuyDetector™ is faking transactions.\n🚨 No real wallet is being watched."
        if GIF_URL:
            await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=test_text, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=CHAT_ID, text=test_text, parse_mode="Markdown")
        print("✅ Test message sent to Telegram!")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

async def check_transactions():
    print("🧪 Simulated Solana BuyDetector™ running...")

    fake_sigs = [
        "simulatedsig001",
        "simulatedsig002",
        "simulatedsig003"
    ]
    index = 0

    while True:
        try:
            sig = fake_sigs[index % len(fake_sigs)]
            index += 1

            from_addr = f"SimulatedFrom{index:03d}xxxxxxxxxxxxxxxxxxxx"
            to_addr = MONITORED_WALLET
            sol_amount = round(0.5 + index * 0.37, 4)

            sol_price = await get_sol_price()
            usd_value = sol_amount * sol_price
            bullets = generate_bullets(sol_amount)

            msg_text = (
                f"🪙 *Simulated $BabyGOV contribution detected!*\n\n"
                f"🔁 From: `{from_addr}`\n"
                f"📥 To: `{to_addr}`\n"
                f"🟨 *Amount:*\n"
                f"┌────────────────────────────┐\n"
                f"│  {sol_amount:.4f} SOL (~${usd_value:,.2f})  │\n"
                f"└────────────────────────────┘\n"
                f"{bullets}\n\n"
                f"🔗 [Simulated TX](https://solscan.io/tx/{sig})\n\n"
                f"───────────────\n"
                f"🤖 𝓑𝓾𝔂𝓓𝓮𝓽𝓮𝓬𝓽𝓸𝓻™ Simulated\n"
                f"🔧 by ReactLAB"
            )

            if GIF_URL:
                await bot.send_animation(chat_id=CHAT_ID, animation=GIF_URL, caption=msg_text, parse_mode="Markdown")
            else:
                await bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown")

            print(f"✅ Simulated TX posted: {sig}")

        except Exception as e:
            print(f"⚠️ Simulated TX error: {e}")

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(test_telegram_message())
    asyncio.run(check_transactions())
