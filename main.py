import os
import sys
import asyncio
import importlib
import git
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv

# .env yükle
load_dotenv()

# Değişkenler
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GIT_REPO = os.getenv("GIT_REPO_URL")

# --- İKİ İSTEMCİYİ BAŞLAT ---
# 1. Userbot (Senin hesabın)
client = TelegramClient('userbot_session', API_ID, API_HASH)
# 2. Yardımcı Bot (Inline butonlar için)
bot = TelegramClient('bot_session', API_ID, API_HASH)

# --- RENKLİ LOGLAR ---
def log(text):
    print(f"\033[92m[BİLGİ]\033[0m {text}")

# --- YARDIMCI BOT (INLINE) TARAFI ---
@bot.on(events.InlineQuery)
async def inline_handler(event):
    builder = event.builder
    query = event.text

    if query == "help_menu":
        # Butonlu Yardım Menüsü
        result = builder.article(
            title="Userbot Yardım",
            text="**🤖 Gelişmiş Userbot Yardım Menüsü**\n\nAşağıdaki butonları kullanarak kategorilere göz atabilirsin.",
            buttons=[
                [Button.inline("📜 Komutlar", data="cmds"), Button.inline("ℹ️ Hakkında", data="about")],
                [Button.inline("❌ Kapat", data="close")]
            ]
        )
        await event.answer([result])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    # Butonlara tıklandığında ne olacağını belirler
    data = event.data.decode('utf-8')
    
    if data == "cmds":
        await event.edit(
            "**🛠 Temel Komutlar:**\n\n"
            "`.alive` - Botun çalışıp çalışmadığını kontrol eder.\n"
            "`.pinstall <yanıt>` - Bir .py modülünü yükler.\n"
            "`.update` - Botu GitHub üzerinden günceller.\n"
            "`.start` - Bot durumunu ve istatistikleri gösterir.",
            buttons=[[Button.inline("🔙 Geri", data="back")]]
        )
    elif data == "about":
        await event.edit(
            "**👤 Userbot Hakkında**\n\n"
            "Bu bot modüler bir yapıya sahiptir ve Telegram deneyimini geliştirmek için tasarlanmıştır.",
            buttons=[[Button.inline("🔙 Geri", data="back")]]
        )
    elif data == "back":
        await event.edit(
            "**🤖 Gelişmiş Userbot Yardım Menüsü**\n\nSeçimini yap:",
            buttons=[
                [Button.inline("📜 Komutlar", data="cmds"), Button.inline("ℹ️ Hakkında", data="about")],
                [Button.inline("❌ Kapat", data="close")]
            ]
        )
    elif data == "close":
        await event.delete()

# --- USERBOT (KULLANICI) TARAFI ---

# 1. START KOMUTU
@client.on(events.NewMessage(outgoing=True, pattern=r'\.start'))
async def start_cmd(event):
    await event.edit(
        "**⚡ Userbot Çevrimiçi!**\n\n"
        f"🐍 **Python:** `{sys.version.split()[0]}`\n"
        "🛰 **Telethon:** `Son Sürüm`\n"
        "Modüler sistem aktif ve komut bekliyor."
    )

# 2. HELP KOMUTU (Inline Bağlantılı)
@client.on(events.NewMessage(outgoing=True, pattern=r'\.help'))
async def help_cmd(event):
    # Botun kullanıcı adını al
    bot_user = await bot.get_me()
    results = await client.inline_query(bot_user.username, "help_menu")
    await results[0].click(event.chat_id)
    await event.delete() # .help yazısını siler

# 3. UPDATE KOMUTU (GitHub)
@client.on(events.NewMessage(outgoing=True, pattern=r'\.update'))
async def update_cmd(event):
    await event.edit("🔄 **GitHub üzerinden güncellemeler kontrol ediliyor...**")
    try:
        repo = git.Repo(os.getcwd())
        origin = repo.remotes.origin
        origin.fetch()
        
        if repo.head.commit != origin.refs.main.commit:
            await event.edit("📥 **Güncelleme bulundu! İndiriliyor...**")
            origin.pull()
            await event.edit("✅ **Güncellendi! Bot yeniden başlatılıyor...**")
            # Scripti yeniden başlat
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await event.edit("✅ **Bot zaten en güncel sürümde!**")
    except Exception as e:
        await event.edit(f"❌ **Güncelleme Hatası:** `{e}`")

# 4. PINSTALL (Modül Yükleyici)
@client.on(events.NewMessage(outgoing=True, pattern=r'\.pinstall'))
async def pinstall_cmd(event):
    if not event.reply_to_msg_id:
        return await event.edit("⚠️ Lütfen bir `.py` dosyasına yanıt vererek bu komutu kullanın.")
    
    reply = await event.get_reply_message()
    if reply.media and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        file_path = await reply.download_media(file="modules/")
        mod_name = os.path.basename(file_path).replace('.py', '')
        
        try:
            # Modülü dinamik yükle
            spec = importlib.util.spec_from_file_location(mod_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Eğer modülün içinde 'handler' adında bir event varsa ekle
            if hasattr(mod, 'handler'):
                client.add_event_handler(mod.handler)
                
            await event.edit(f"✅ **{mod_name}** modülü başarıyla yüklendi!")
        except Exception as e:
            await event.edit(f"❌ Modül yüklenemedi: `{e}`")
    else:
        await event.edit("❌ Lütfen geçerli bir Python dosyası gönderin.")

# --- BAŞLATMA ---
log("Userbot ve Yardımcı Bot başlatılıyor...")
client.start()
bot.start(bot_token=BOT_TOKEN)

try:
    log("Sistem Aktif!")
    client.run_until_disconnected()
finally:
    client.disconnect()
    bot.disconnect()
