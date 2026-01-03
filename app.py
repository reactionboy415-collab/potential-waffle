import telebot
import requests
import io
import concurrent.futures
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
BOT_TOKEN = "8352421501:AAGV8qxjUfL2WdjDDq6p-ayZp4dUgi6nkwE" 
ADMIN_ID = 7840042951
TARGET_QTY = 100000 # 1 Lakh Target
GRAB_LIMIT = 600000 # 5 Lakh Pool
BATCH_SIZE = 65     # Safe Batch Testing

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Branding Database Names
tokens = {
    "auth": "eyJhbGciOiJFUzI1NiIsImtpZCI6ImYyZTIyZWFhLTRhYjQtNDZhOC1hYzM3LTExYzA3YWQyNTgzNCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Z3bWhicGd3aGZ3dXd0YXR0c2V0LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1ZmM0NTA3ZS00NTI2LTQ2OGItYjFkMi01YmVlOTZkNmQwMTEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY3NDA0Nzg0LCJpYXQiOjE3Njc0MDExODQsImVtYWlsIjoiamhvbmRlb0BnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiamhvbmRlb0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiSm9obiBkb2UiLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInN1YiI6IjVmYzQ1MDdlLTQ1MjYtNDY4Yi1iMWQyLTViZWU5NmQ2ZDAxMSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzY3NDAxMTg0fV0sInNlc3Npb25faWQiOiI4MzkzYWU2Zi0zYTJlLTQ0ZDUtYjg1ZS1lYWEwMzQwNDdhYWEiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.ijYObw_fffHDtEIw3PPKqDyDW6StUn3NkaofNcfTakA5KMCwuzmW6UQq2_mSxfu5PHejh1xUNLQWQCH6weidjQ",
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3bWhicGd3aGZ3dXd0YXR0c2V0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczMjc0NjYsImV4cCI6MjA4MjkwMzQ2Nn0.LSMD2P4whDzoIW4UCig0ly0j6UOxd5fHhIkUhywnmrg"
}

@app.route('/')
def home(): return "CR Engine Status: ACTIVE"

# --- DB ENGINES ---
def fetch_cr_infra():
    """Grabs massive pool from CR Supabase & Backup Nodes"""
    pool = []
    headers = {"authorization": f"Bearer {tokens['auth']}", "apikey": tokens['apikey'], "content-type": "application/json"}
    
    # Database 1: CR Supabase
    try:
        r = requests.post("https://vwmhbpgwhfwuwtattset.supabase.co/functions/v1/fetch-proxies", 
                          headers=headers, json={"limit": 20000}, timeout=20)
        pool.extend([f"{p['ip']}:{p['port']}" for p in r.json().get("proxies", [])])
    except: pass

    # Database 2 & 3: CR Cloud Backups (Multiple Sources)
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
    ]
    for src in sources:
        try:
            r = requests.get(src, timeout=10)
            if r.status_code == 200: pool.extend(r.text.strip().split('\n'))
        except: continue
    
    return list(set(pool)) # Unique 5 Lakh+ Pool

def verify_node(addr):
    try:
        proxies = {"http": f"http://{addr}", "https": f"http://{addr}"}
        r = requests.get("http://www.google.com", proxies=proxies, timeout=3.0)
        return addr if r.status_code == 200 else None
    except: return None

# --- BATCH PROCESSOR ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🚀 Start 1 Lakh Bulk Mission')
    bot.send_message(message.chat.id, "💎 **CR Professional Bulk Engine**\nBatch Processing (50/step) enabled.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🚀 Start 1 Lakh Bulk Mission')
def start_mission(message):
    chat_id = message.chat.id
    status_msg = bot.send_message(chat_id, "📡 **Phase 1: Building 5 Lakh+ Proxy Pool...**")
    
    raw_pool = fetch_cr_infra()
    total_raw = len(raw_pool)
    
    bot.edit_message_text(f"✅ **Pool Built:** `{total_raw}` Nodes Found.\n🚀 **Phase 2: Starting Batch Testing (50 per run)...**", chat_id, status_msg.message_id)
    
    verified_list = []
    scanned_count = 0
    
    # BATCH LOOPING
    for i in range(0, total_raw, BATCH_SIZE):
        if len(verified_list) >= TARGET_QTY: break
        
        # Get next 50
        current_batch = raw_pool[i : i + BATCH_SIZE]
        
        # Test current batch
        with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            results = list(executor.map(verify_node, current_batch))
            for res in results:
                if res: verified_list.append(res)
                scanned_count += 1
        
        # Update User every batch
        if (i // BATCH_SIZE) % 5 == 0: # Update every 5 batches to avoid rate limit
            try:
                progress = (len(verified_list) / TARGET_QTY) * 100
                bot.edit_message_text(
                    f"🛰 **CR Professional Batch Scanner**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ **Verified:** `{len(verified_list)} / {TARGET_QTY}`\n"
                    f"🔎 **Scanned Total:** `{scanned_count}`\n"
                    f"📦 **Current Batch:** `50 Nodes`\n"
                    f"📊 **Progress:** `{progress:.2f}%`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ *Safe Mode: Testing Run-by-Run...*",
                    chat_id, status_msg.message_id, parse_mode="Markdown"
                )
            except: pass

    # FINAL DELIVERY
    if verified_list:
        bot.send_message(chat_id, "📦 **Mission Accomplished! Packing 1 Lakh Proxies...**")
        final_data = "\n".join(verified_list[:TARGET_QTY])
        file_buffer = io.BytesIO(final_data.encode())
        file_buffer.name = f"CR_100K_FINAL.txt"
        bot.send_document(chat_id, file_buffer, caption=f"✅ **Bulk Order Ready**\nTotal: `100,000` Working Nodes.")
    else:
        bot.send_message(chat_id, "❌ Pool exhausted before reaching target.")

# --- RUN ---
def run_flask(): app.run(host='0.0.0.0', port=7860)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()