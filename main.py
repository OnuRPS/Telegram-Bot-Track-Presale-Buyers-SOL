import os
import asyncio
import aiohttp
import csv
import datetime
import warnings
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature
from telegram import Bot
from dotenv import load_dotenv

warnings.simplefilter("always", RuntimeWarning)

# === CONFIG ===
load_dotenv()
SOLANA_RPC = os.getenv("SOLANA_RPC")
BABYGOV_MINT = "9wSAERFBoG2S7Hwa1xq64h2S6tZCR5KoTXBS1pwep7Gf"
BABYGOV_LP = "6Ch1KUEDm8i8JcSCTnAUS72FC7FJzWuKZYEqZ5Pe67KE"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = [int(x) for x in os.getenv("CHAT_IDS", "").split(",") if x]
bot = Bot(token=TELEGRAM_TOKEN)
GIF_URL = "https://pandabao.org/wp-content/uploads/2025/05/babaygov.gif"
CSV_FILE = "babygov_buys.csv"
last_seen_sigs = set()
trend_data = []

# === UTILS ===
def shorten(addr):
    return f"{addr[:6]}...{addr[-4:]}" if addr else "Unknown"

def mini_chart(amount):
    trend_data.append(amount)
    if len(trend_data) > 5:
        trend_data.pop(0)
    return "".join(["⬆️" if x > trend_data[i - 1] else "⬇️" for i, x in enumerate(trend_data) if i > 0])

def log_csv(sig, buyer, amount, sol, usd, rank):
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Signature", "Buyer", "BabyGOV", "SOL", "USD", "Rank"])
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([sig, buyer, round(amount, 4), round(sol, 6), round(usd, 2), rank or "New Wallet"])

async def get_buyer_rank(mint, buyer):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://pro-api.solscan.io/v1.0/token/holders?tokenAddress={mint}&limit=50"
            headers = {"Authorization": f"Bearer {os.getenv('SOLSCAN_API_KEY')}"}
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                for i, holder in enumerate(data.get("data", [])):
                    if holder.get("owner") == buyer:
                        return i + 1
    except Exception as e:
        print(f"[RANK ERROR] {e}")
    return None

async def send_telegram(buyer, amount, sol_spent, sig, rank):
    usd = round(sol_spent * 175.0, 2)
    if usd < 10:
        print(f"[SKIP] Sub 10$: {usd:.2f}")
        return

    trend = mini_chart(amount)
    msg = f"""🟢 BabyGOV Buy Detected (BabyGOV/SOL) {trend}

🔀 {sol_spent:.6f} SOL (~${usd})
🔀 {amount:,.2f} BabyGOV
{"🏅 Rank: #" + str(rank) if rank else "👤 New Wallet"}

👤 [{shorten(buyer)}](https://solscan.io/account/{buyer})
🔗 [View Tx](https://solscan.io/tx/{sig})

🛒 [Buy on Raydium](https://raydium.io/swap/?inputMint={BABYGOV_MINT}&outputMint=sol)
📈 [Chart on DEXTools](https://www.dextools.io/app/en/solana/pair-explorer/{BABYGOV_LP})

🧐 Powered by @BabyGovBot"""

    for chat_id in CHAT_IDS:
        try:
            await bot.send_animation(chat_id=chat_id, animation=GIF_URL, caption=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"[❌ Telegram Error] {e}")

async def fetch_tx_details(sig):
    await asyncio.sleep(0.3)
    async with aiohttp.ClientSession() as session:
        async with session.post(SOLANA_RPC, json={
            "jsonrpc": "2.0", "id": 1, "method": "getTransaction",
            "params": [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        }) as resp:
            return (await resp.json()).get("result")

# === MONITORING LOOP ===
async def monitor_babygov():
    print("🟢 Monitorizare activă pe LP BabyGOV/SOL (Raydium pool)...")
    client = AsyncClient(SOLANA_RPC)
    lp_pubkey = Pubkey.from_string(BABYGOV_LP)

    while True:
        try:
            resp = await client.get_signatures_for_address(lp_pubkey, limit=15)
            txs = resp.value
            for tx in reversed(txs):
                sig = str(tx.signature)
                if sig in last_seen_sigs:
                    continue
                last_seen_sigs.add(sig)

                if tx.block_time is None:
                    continue
                now = datetime.datetime.now(datetime.timezone.utc)
                tx_time = datetime.datetime.fromtimestamp(tx.block_time, datetime.timezone.utc)
                age = (now - tx_time).total_seconds()
                if age > 600:
                    print(f"[SKIP] Tranzacție prea veche: {tx_time} (age {int(age)}s)")
                    continue

                print(f"🔍 Procesare TX: {sig}")
                tx_data = await fetch_tx_details(sig)
                if not tx_data:
                    continue

                try:
                    meta = tx_data["meta"]
                    pre = meta.get("preTokenBalances", [])
                    post = meta.get("postTokenBalances", [])
                    buyer = None
                    received = 0
                    for i in range(len(pre)):
                        if post[i]["mint"] == BABYGOV_MINT:
                            decimals = int(post[i]["uiTokenAmount"]["decimals"])
                            pre_amt = float(pre[i]["uiTokenAmount"]["amount"])
                            post_amt = float(post[i]["uiTokenAmount"]["amount"])
                            delta = (post_amt - pre_amt) / (10 ** decimals)
                            if delta > 0:
                                received = delta
                                buyer = post[i]["owner"]
                                break

                    if not buyer or received == 0:
                        continue

                    pre_sol = meta.get("preBalances", [])
                    post_sol = meta.get("postBalances", [])
                    sol_spent = max([(pre_sol[i] - post_sol[i]) / 1e9 for i in range(min(len(pre_sol), len(post_sol))) if pre_sol[i] > post_sol[i]], default=0)

                    usd = sol_spent * 175
                    if usd >= 2:
                        rank = await get_buyer_rank(BABYGOV_MINT, buyer)
                        log_csv(sig, buyer, received, sol_spent, usd, rank)
                        await send_telegram(buyer, received, sol_spent, sig, rank)
                    else:
                        print(f"[SKIP] Sub 10$: {usd:.2f}")
                except Exception as e:
                    print(f"[Eroare TX] {e}")

        except Exception as e:
            print(f"[RPC ERROR] {e}")
        await asyncio.sleep(4)

asyncio.run(monitor_babygov())
