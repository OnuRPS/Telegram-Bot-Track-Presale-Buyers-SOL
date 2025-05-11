import os
import asyncio
import aiohttp
import csv
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from telegram import Bot
from dotenv import load_dotenv

# === CONFIG ===
load_dotenv()
SOLANA_RPC = os.getenv("SOLANA_RPC")
BABYGOV_MINT = "9wSAERFBoG2S7Hwa1xq64h2S6tZCR5KoTXBS1pwep7Gf"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = [int(x) for x in os.getenv("CHAT_IDS", "").split(",") if x]
bot = Bot(token=TELEGRAM_TOKEN)
GIF_URL = "https://pandabao.org/wp-content/uploads/2025/05/babaygov.gif"

CSV_FILE = "babygov_buys.csv"
trend_data = []

# === INIT CSV ===
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Signature", "Buyer", "BabyGOV", "SOL", "USD_EST", "Rank"])

def shorten_address(addr):
    return f"{addr[:6]}...{addr[-4:]}" if addr else "Unknown"

def mini_chart(amount):
    global trend_data
    trend_data.append(amount)
    if len(trend_data) > 5:
        trend_data.pop(0)
    return "".join(["⬆️" if x > trend_data[i - 1] else "⬇️" for i, x in enumerate(trend_data) if i > 0])

async def get_buyer_rank(mint, buyer):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://public-api.solscan.io/token/holders?tokenAddress={mint}&limit=50"
            async with session.get(url) as resp:
                data = await resp.json()
                for i, holder in enumerate(data.get("data", [])):
                    if holder.get("owner") == buyer:
                        return i + 1
        return None
    except Exception:
        return None

def log_to_csv(sig, buyer, amount, sol, usd, rank):
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([sig, buyer, round(amount, 4), round(sol, 6), round(usd, 2), rank or "New Wallet"])

async def send_to_telegram(buyer, amount, sol_spent, price, signature, rank):
    total_usd = round(sol_spent * 175.0, 2)
    token_usd = round(amount * price, 6)
    trend = mini_chart(amount)
    msg = f"""
🟢 BabyGOV Buy Detected (BabyGOV/SOL) {trend}

🔀 {sol_spent:.6f} SOL (~${total_usd})
🔀 {amount:.2f} BabyGOV (~${token_usd})
{f"🏅 Rank: #{rank}" if rank else "👤 New Wallet"}

👤 {shorten_address(buyer)} (https://solscan.io/account/{buyer}) | [Txn](https://solscan.io/tx/{signature})

🛒 [Buy on Raydium](https://raydium.io/swap/?inputMint={BABYGOV_MINT}&outputMint=sol)
📈 [Chart on DEXTools](https://www.dextools.io/app/en/solana/pair-explorer/6Ch1KUEDm8i8JcSCTnAUS72FC7FJzWuKZYEqZ5Pe67KE)

🧠 Powered by @BabyGovBot
"""
    print("[📤 Telegram] Trimit mesaj + GIF animat...")
    for chat_id in CHAT_IDS:
        try:
            await bot.send_animation(
                chat_id=chat_id,
                animation=GIF_URL,
                caption=msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[❌ Telegram error în {chat_id}]: {e}")

async def fetch_tx_details(signature):
    async with aiohttp.ClientSession() as session:
        async with session.post(SOLANA_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }) as resp:
            data = await resp.json()
            return data.get("result")

async def monitor_babygov():
    client = AsyncClient(SOLANA_RPC)
    mint_pubkey = Pubkey.from_string(BABYGOV_MINT)
    last_signature = None

    print("🟢 Monitorizare activă pe BabyGOV/SOL...")

    while True:
        try:
            resp = await client.get_signatures_for_address(mint_pubkey, limit=5)
            txs = resp.value
            for tx in txs:
                sig = str(tx.signature)
                if sig == last_signature:
                    break

                print(f"🔍 Verific tranzacție nouă: {sig}")
                tx_data = await fetch_tx_details(sig)
                if not tx_data:
                    continue

                try:
                    meta = tx_data["meta"]
                    pre_token_balances = meta.get("preTokenBalances", [])
                    post_token_balances = meta.get("postTokenBalances", [])
                    pre_balances_sol = meta.get("preBalances", [])
                    post_balances_sol = meta.get("postBalances", [])
                    account_keys = tx_data["transaction"]["message"]["accountKeys"]

                    received = 0
                    buyer = None
                    sol_spent = 0

                    for pre, post in zip(pre_token_balances, post_token_balances):
                        if post["mint"] == BABYGOV_MINT:
                            pre_amt = float(pre.get("uiTokenAmount", {}).get("amount", 0))
                            post_amt = float(post.get("uiTokenAmount", {}).get("amount", 0))
                            decimals = int(post["uiTokenAmount"]["decimals"])
                            delta = (post_amt - pre_amt) / (10 ** decimals)
                            if delta > 0:
                                received = delta
                                buyer = post["owner"]

                    if received > 0 and buyer:
                        try:
                            buyer_index = account_keys.index(buyer)
                            if buyer_index < len(pre_balances_sol) and buyer_index < len(post_balances_sol):
                                sol_spent = (pre_balances_sol[buyer_index] - post_balances_sol[buyer_index]) / 1e9
                        except ValueError:
                            pass

                        if sol_spent == 0:
                            for i in range(len(pre_balances_sol)):
                                diff = pre_balances_sol[i] - post_balances_sol[i]
                                if diff > 0:
                                    sol_spent = diff / 1e9
                                    break

                        token_price = sol_spent / received if received > 0 else 0.0001
                        rank = await get_buyer_rank(BABYGOV_MINT, buyer)
                        print(f"✅ Buy detectat: {received:.2f} BabyGOV cu {sol_spent:.6f} SOL")
                        log_to_csv(sig, buyer, received, sol_spent, sol_spent * 175, rank)
                        await send_to_telegram(buyer, received, sol_spent, token_price, sig, rank)

                except Exception as e:
                    print(f"[⚠️ Eroare analiză]: {e}")

                last_signature = sig
            await asyncio.sleep(10)
        except Exception as e:
            print(f"[❌ Eroare RPC]: {e}")
            await asyncio.sleep(30)

asyncio.run(monitor_babygov())
