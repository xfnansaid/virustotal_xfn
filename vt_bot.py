import os
import httpx
import logging
import asyncio
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- SECURE CREDENTIALS ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY")

# --- NEW: Dummy Web Server to satisfy Render ---
def keep_alive():
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot is alive and running!")
            
        def log_message(self, format, *args):
            pass # Disables web server logs to keep your terminal clean

    # Render automatically assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

# Start the web server in a background thread
threading.Thread(target=keep_alive, daemon=True).start()
# -----------------------------------------------

# Mixed Trivia Library
TRIVIA_BANK = [
    {"q": "Which club has won the most UEFA Champions League titles?", "a": "Real Madrid 👑"},
    {"q": "What is the rarest blood type in the human population?", "a": "AB Negative 🩸"},
    {"q": "Which team holds the record for being the only 'Invincibles' in the Premier League era?", "a": "Arsenal (2003-04) 🔴⚪"},
    {"q": "What is the hardest natural substance on Earth?", "a": "Diamond 💎"},
    {"q": "Who is the all-time top scorer in the UEFA Champions League?", "a": "Cristiano Ronaldo ⚽"},
    {"q": "Which planet in our solar system has the most moons?", "a": "Saturn 🪐"}
]

# Hacker Terminal Boot Sequence
HACKER_STEPS = [
    "[+] Bypassing mainframe firewall...",
    "[+] Decrypting SSL certificates...",
    "[+] Injecting payload into threat database...",
    "[+] Cross-referencing global malware registries...",
    "[+] Executing deep packet inspection..."
]

# ... (Keep your start_command, scan_url, and the if __name__ == '__main__': block exactly the same as before!)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Hello! 🛡️ I am your VirusTotal Scanner Bot.\n\n"
        "Send me any URL, and I will scan it across dozens of antivirus engines to tell you if it's safe."
    )
    await update.message.reply_text(welcome_text)

async def scan_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    if not user_message.startswith("http"):
        user_url = f"http://{user_message}"
    else:
        user_url = user_message

    # 1. Select random trivia
    trivia = random.choice(TRIVIA_BANK)
    
    # 2. Build the initial message
    dynamic_text = f"🧠 **Trivia Time:** {trivia['q']}\n\n`[+] Initiating secure connection...`"
    status_msg = await update.message.reply_text(dynamic_text, parse_mode="Markdown")

    vt_submit_url = "https://www.virustotal.com/api/v3/urls"
    headers = {
        "accept": "application/json",
        "x-apikey": VIRUSTOTAL_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {"url": user_url}
            post_response = await client.post(vt_submit_url, data=payload, headers=headers)
            
            if post_response.status_code != 200:
                await status_msg.edit_text(f"❌ API Error: {post_response.status_code}")
                return
            
            analysis_id = post_response.json().get("data", {}).get("id")
            if not analysis_id:
                await status_msg.edit_text("❌ Failed to get an analysis ID.")
                return

            vt_analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            
            # 3. The Polling Loop with Terminal Updates
            for attempt in range(5):
                await asyncio.sleep(3)
                
                # Append the next hacker step to the dynamic text
                step = HACKER_STEPS[attempt % len(HACKER_STEPS)]
                dynamic_text += f"\n`{step}`"
                
                # Update the message so the user sees the terminal "scrolling"
                await status_msg.edit_text(dynamic_text, parse_mode="Markdown")
                
                get_response = await client.get(vt_analysis_url, headers=headers)
                if get_response.status_code != 200:
                    return
                
                result_data = get_response.json().get("data", {}).get("attributes", {})
                status = result_data.get("status")
                
                if status == "completed":
                    stats = result_data.get("stats", {})
                    malicious = stats.get("malicious", 0)
                    suspicious = stats.get("suspicious", 0)
                    harmless = stats.get("harmless", 0)
                    undetected = stats.get("undetected", 0)
                    
                    total_scanners = malicious + suspicious + harmless + undetected
                    
                    if malicious > 0 or suspicious > 0:
                        safety_status = "⚠️ **WARNING: Malicious/Suspicious Activity Detected!**"
                    else:
                        safety_status = "✅ **CLEAN: No threats detected.**"
                    
                    # 4. The Final Report + Trivia Answer
                    report = (
                        f"**VirusTotal Scan Report**\n"
                        f"URL: `{user_url}`\n\n"
                        f"{safety_status}\n\n"
                        f"🚨 **Malicious:** {malicious}\n"
                        f"🤔 **Suspicious:** {suspicious}\n"
                        f"🛡️ **Harmless:** {harmless}\n"
                        f"🤷 **Undetected:** {undetected}\n\n"
                        f"_Scanned by {total_scanners} engines._\n\n"
                        f"💡 **Answer:** {trivia['a']}"
                    )
                    
                    await status_msg.edit_text(report, parse_mode="Markdown")
                    return
            
            await status_msg.edit_text("⏳ Scan taking too long. Please check the VirusTotal website directly.")

        except Exception as e:
            await status_msg.edit_text(f"❌ An error occurred: {str(e)}")

if __name__ == '__main__':
    # Build and start the Telegram bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, scan_url))
    
    print("Bot is running...")
    app.run_polling()
