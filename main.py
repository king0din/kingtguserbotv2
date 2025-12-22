import os
import sys
import asyncio
import importlib
import git
import glob
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
client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

# --- LOG FONKSİYONU ---
def log(text):
    print(f"\033[92m[BİLGİ]\033[0m {text}")

# --- DÜZELTİLMİŞ MODÜL YÜKLEYİCİ ---
async def load_plugins(plugin_name):
    """Modülleri yükler ve register ile işaretlenmiş eventleri ekler."""
    try:
        path = f"modules/{plugin_name}.py"
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Modül içindeki her nesneyi tara
        count = 0
        for name in dir(mod):
            obj = getattr(mod, name)
            
            # KRİTİK DÜZELTME: Nesnenin bir events.register örneği olup olmadığını kontrol et
            if isinstance(obj, events.register):
                client.add_event_handler(obj)
                count += 1
        
        if count > 0:
            log(f"✅ {plugin_name} yüklendi ({count} komut)")
            return True
        else:
            log(f"⚠️ {plugin_name} yüklendi ama çalıştırılabilir komut bulunamadı.")
            return False

    except Exception as e:
        print(f"❌ Hata ({plugin_name}): {e}")
        return False

# --- YARDIMCI BOT (INLINE) ---
@bot.on(events.InlineQuery)
async def inline_handler(event):
    builder = event.builder
    query = event.text
    if query == "help_menu":
        result = builder.article(
            title="Userbot Yardım",
            text="**🤖 Userbot Kontrol Paneli**",
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
        await event.edit("**Komutlar:**\n`.alive`, `.pinstall`, `.update`, `.start`", buttons=[[Button.inline("🔙 Geri", data="back")]])
    elif data == "back":
        await event.edit("**🤖 Panel**", buttons=[[Button.inline("📜 Komutlar", data="cmds"), Button.inline("ℹ️ Hakkında", data="about")], [Button.inline("❌ Kapat", data="close")]])
    elif data == "close":
        await event.delete()

# --- USERBOT EVENTLERİ ---

@client.on(events.NewMessage(outgoing=True, pattern=r'\.start'))
async def start_cmd(event):
    await event.edit("**⚡ Userbot Aktif!**")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.help'))
async def help_cmd(event):
    bot_user = await bot.get_me()
    try:
        results = await client.inline_query(bot_user.username, "help_menu")
        await results[0].click(event.chat_id)
        await event.delete()
    except Exception as e:
        await event.edit(f"⚠️ Hata: Inline bot cevap vermedi. `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.update'))
async def update_cmd(event):
    await event.edit("🔄 Güncelleniyor...")
    try:
        repo = git.Repo(os.getcwd())
        repo.remotes.origin.pull()
        await event.edit("✅ Yeniden başlatılıyor...")
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await event.edit(f"❌ Hata: `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.pinstall'))
async def pinstall_cmd(event):
    if not event.reply_to_msg_id:
        return await event.edit("⚠️ Bir `.py` dosyasına yanıt verin.")
    
    reply = await event.get_reply_message()
    if reply.media and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        file_path = await reply.download_media(file="modules/")
        mod_name = os.path.basename(file_path).replace('.py', '')
        
        await event.edit(f"📥 `{mod_name}` işleniyor...")
        
        # Dosya indirildikten sonra yüklemeyi dene
        if await load_plugins(mod_name):
            await event.edit(f"✅ `{mod_name}` başarıyla yüklendi!")
        else:
            await event.edit(f"⚠️ `{mod_name}` yüklendi ama içinde aktif komut bulunamadı.")
    else:
        await event.edit("❌ Geçersiz dosya.")

# --- BAŞLATMA ---
print("--- Userbot Başlatılıyor ---")
client.start()
bot.start(bot_token=BOT_TOKEN)

# modules klasöründeki mevcut dosyaları yükle
if not os.path.exists("modules"):
    os.makedirs("modules")

mod_files = glob.glob("modules/*.py")
log(f"Bulunan modül sayısı: {len(mod_files)}")

# Mevcut event döngüsünde yükleme yapıyoruz
loop = asyncio.get_event_loop()
for file in mod_files:
    mod_name = os.path.basename(file).replace(".py", "")
    loop.run_until_complete(load_plugins(mod_name))

log("Sistem hazır!")
client.run_until_disconnected()
