import requests, urllib3, os, re, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from github import Github # Pastikan install dengan: pip install PyGithub

urllib3.disable_warnings()

# --- [DATA KONFIGURASI] ---
TOKEN = "8246631249:AAGXgyD1zucoy-fv5qghTZ7MnPhj4c7aG_Y"
USER_BOLEH_AKSES = [7038651668, 5853539049] 

# GANTI DI SINI PAKE DATA BARU LU:
GITHUB_TOKEN = "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" 
REPO_NAME = "username_github_lu/cekbot" # Ganti jadi user_github/cekbot

PATH_MENTAHAN = "mentahan.html"

PROXIES = {"http": None, "https": None}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# --- [CORE FUNCTIONS] ---
def get_current_links():
    if not os.path.exists(PATH_MENTAHAN): return []
    with open(PATH_MENTAHAN, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r"//LIST_START(.*?)//LIST_END", content, flags=re.DOTALL)
    if match:
        raw_lines = match.group(1).strip().split("\n")
        return [re.sub(r'[",\s]', '', l) for l in raw_lines if l.strip()]
    return []

def save_links_to_html(links):
    if not os.path.exists(PATH_MENTAHAN): return False
    with open(PATH_MENTAHAN, 'r', encoding='utf-8') as f:
        content = f.read()
    formatted_links = ",\n            ".join([f'"{l}"' for l in links]) if links else ""
    pattern = r"(//LIST_START).*?(//LIST_END)"
    replacement = rf"\1\n            {formatted_links}\n            \2"
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open(PATH_MENTAHAN, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

# --- [FUNGSI CEK NAWALA] ---
async def cek_nawala_job(context: ContextTypes.DEFAULT_TYPE):
    links = get_current_links()
    if not links: return 

    NAWALA_URLS = ["internet-positif", "uzone.id", "aduankonten", "stoppornografi", "telkomsel.com/not-found", "rancangan_peraturan_menkominfo"]
    
    report = "🚨 **DOMAIN ALERT (TERDETEKSI MASALAH!):**\n\n"
    ada_masalah = False

    for link in links:
        try:
            res = requests.get(link, headers=HEADERS, timeout=15, verify=True, allow_redirects=True, proxies=PROXIES)
            if any(target in res.url.lower() for target in NAWALA_URLS) or res.status_code != 200:
                report += f"• `{link}` -> 🚫 **Masalah/Blokir**\n"
                ada_masalah = True
        except:
            report += f"• `{link}` -> 💀 **Mati/RTO**\n"
            ada_masalah = True

    if ada_masalah:
        for uid in USER_BOLEH_AKSES:
            try: await context.bot.send_message(chat_id=uid, text=report, parse_mode="Markdown")
            except: pass

# --- [TELEGRAM COMMANDS] ---
async def update_semua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in USER_BOLEH_AKSES: return
    msg = await update.message.reply_text("⏳ Menyinkronkan ke GitHub (Cloudflare akan update)...")
    
    try:
        with open(PATH_MENTAHAN, 'r', encoding='utf-8') as f: content = f.read()
        
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        # Cari file index.html di repo
        file_to_update = repo.get_contents("index.html")
        repo.update_file(file_to_update.path, "Update via bot", content, file_to_update.sha)
        
        await msg.edit_text("✅ Berhasil! Cloudflare akan melakukan auto-deploy dalam 30 detik.")
    except Exception as e:
        await msg.edit_text(f"❌ Error GitHub: {str(e)}")

# --- [MAIN] ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("list", list_link)) # Pastikan fungsi list_link dkk ada di atas
    app.add_handler(CommandHandler("tambah", tambah))
    app.add_handler(CommandHandler("hapus", hapus))
    app.add_handler(CommandHandler("update_semua", update_semua))

    job_queue = app.job_queue
    job_queue.run_repeating(cek_nawala_job, interval=3600, first=10) 

    print(">>> BOT GUARDIAN (CLOUDFLARE MODE) AKTIF <<<")
    app.run_polling()