import os
import sys
import asyncio
import importlib
import git
import glob
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv

# .env dosyasından ayarları yükle
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- İSTEMCİLERİ BAŞLAT ---
client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

def log(text):
    print(f"\033[94m[SİSTEM]\033[0m {text}")

# --- MODÜL YÜKLEME MOTORU (KESİN ÇÖZÜM) ---
async def load_plugins(plugin_name):
    """Modülü dinamik olarak yükler ve içindeki komutları bota kaydeder."""
    try:
        # Modül yolu
        path = f"modules/{plugin_name}.py"
        # Mevcut modülü temizle (re-import için)
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]
            
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        count = 0
        for name in dir(mod):
            obj = getattr(mod, name)
            # Telethon @events.register dekoratörü fonksiyona '.events' niteliği ekler.
            # Bu kontrol, sadece 'register' edilmiş fonksiyonları seçmemizi sağlar.
            if hasattr(obj, 'events') and not isinstance(obj, type):
                client.add_event_handler(obj)
                count += 1
        
        if count > 0:
            log(f"✅ {plugin_name} yüklendi ({count} komut aktif)")
            return True
        return False
    except Exception as e:
        print(f"❌ Modül Hatası ({plugin_name}): {e}")
        return False

# --- YARDIMCI BOT (INLINE) ---
@bot.on(events.InlineQuery)
async def inline_handler(event):
    if event.text == "help_menu":
        builder = event.builder
        result = builder.article(
            title="Userbot Kontrol Paneli",
            text="**🤖 Userbot Yardım Menüsü**\n\nModüllerini yönetmek ve komutları görmek için butonları kullan.",
            buttons=[
                [Button.inline("📜 Komutlar", data="cmds"), Button.inline("ℹ️ Hakkında", data="about")],
                [Button.inline("❌ Kapat", data="close")]
            ]
        )
        await event.answer([result])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    if data == "cmds":
        await event.edit("**🛠 Mevcut Komutlar:**\n\n`.alive` - Durum kontrol\n`.start` - İstatistikler\n`.pinstall` - Modül kur\n`.update` - GitHub Güncelleme", buttons=[[Button.inline("🔙 Geri", data="back")]])
    elif data == "about":
        await event.edit("**Userbot v1.0**\n\nTamamen modüler, inline destekli ve GitHub entegreli userbot.", buttons=[[Button.inline("🔙 Geri", data="back")]])
    elif data == "back":
        await event.edit("**🤖 Userbot Yardım Menüsü**", buttons=[[Button.inline("📜 Komutlar", data="cmds"), Button.inline("ℹ️ Hakkında", data="about")], [Button.inline("❌ Kapat", data="close")]])
    elif data == "close":
        await event.delete()

# --- USERBOT TEMEL KOMUTLAR ---

@client.on(events.NewMessage(outgoing=True, pattern=r'\.start'))
async def start_cmd(event):
    await event.edit("🚀 **Userbot Çalışıyor!**\n\nModüller yüklendi, komutlar hazır. Yardım için `.help` yazın.")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.help'))
async def help_cmd(event):
    bot_me = await bot.get_me()
    results = await client.inline_query(bot_me.username, "help_menu")
    await results[0].click(event.chat_id)
    await event.delete()

@client.on(events.NewMessage(outgoing=True, pattern=r'\.update'))
async def update_cmd(event):
    await event.edit("🔄 **Güncellemeler kontrol ediliyor...**")
    try:
        repo = git.Repo(os.getcwd())
        repo.remotes.origin.pull()
        await event.edit("✅ **Güncelleme başarılı! Yeniden başlatılıyor...**")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await event.edit(f"❌ **Hata:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.pinstall'))
async def pinstall_cmd(event):
    if not event.reply_to_msg_id:
        return await event.edit("⚠️ Bir `.py` dosyasına yanıt verin.")
    
    reply = await event.get_reply_message()
    if reply.media and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"): os.makedirs("modules")
        
        file_path = await reply.download_media(file="modules/")
        mod_name = os.path.basename(file_path).replace('.py', '')
        
        await event.edit(f"📥 `{mod_name}` yükleniyor...")
        if await load_plugins(mod_name):
            await event.edit(f"✅ `{mod_name}` başarıyla aktif edildi!")
        else:
            await event.edit(f"❌ `{mod_name}` yüklendi ama çalıştırılabilir komut bulunamadı.")
    else:
        await event.edit("❌ Lütfen geçerli bir Python dosyası gönderin.")

# --- SİSTEMİ ÇALIŞTIR ---
async def startup():
    log("İstemciler başlatılıyor...")
    await client.start()
    await bot.start(bot_token=BOT_TOKEN)
    
    # Mevcut modülleri yükle
    if not os.path.exists("modules"): os.makedirs("modules")
    files = glob.glob("modules/*.py")
    for f in files:
        name = os.path.basename(f).replace('.py', '')
        await load_plugins(name)
    
    log("Userbot Hazır! Komutları kullanabilirsiniz.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
