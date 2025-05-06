🤖 BuyDetector™ – Solana Edition  
### By ReactLAB | Powered by ReactLAB Ecosystem

https://pandabao.org/

**BuyDetector™** is a Telegram bot that monitors real-time **SOL transactions** to a specific wallet – perfect for tracking incoming funds during a presale (e.g., via PinkSale).

---

## 🔍 What the bot does

✅ Monitors the presale pool wallet  
✅ Detects every incoming SOL transaction  
✅ Sends real-time Telegram alerts  
✅ Displays amount in SOL + USD conversion  
✅ Emoji-based visual bullets based on amount  
✅ Direct link to the transaction on Solscan  
✅ Optional animated GIF support  
✅ Cleanly formatted Markdown messages

---

## 🛠️ How to use it

### 1. Clone the repo
```bash
git clone https://github.com/your-username/BuyDetector-Solana.git
cd BuyDetector-Solana
2. Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Set up environment variables
Create a .env file (you can copy from .env.example):

env
Copy
Edit
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=@your_channel_or_-1001234567890
GIF_URL=https://your-optional-gif-link.gif
⚠️ Make sure the bot is an admin in the target Telegram group.

4. Run the bot
bash
Copy
Edit
python3 main.py
🚀 Recommended: Deploy on Railway.app
BuyDetector™ is fully compatible with Railway – a free hosting platform for bots.

Connect your GitHub repo

Add environment variables in Railway's UI

Set the bot to auto-run

Enjoy real-time transaction alerts

📸 Example Telegram Alert
vbnet
Copy
Edit
🪙 New $GOV transaction detected (Solana)

🔁 From: 9qX...7RbL
📥 To: presale_wallet

🟨 Amount:
┌────────────────────┐
│  12.334 SOL (~$1,010.50)  │
└────────────────────┘

🔗 View on Solscan
🤝 Built by ReactLAB
🌐 https://pandabao.org/
🧠 Telegram: https://t.me/PandaBaoOfficial
🔒 Open-source tool for serious crypto builders

🧾 License
MIT – Use it, fork it, improve it.
