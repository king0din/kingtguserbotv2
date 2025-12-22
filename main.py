import os
import sys
import git
import importlib
from telethon import TelegramClient, events
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = TelegramClient('userbot_session', API_ID, API_HASH).start()

# --- GÜNCELLEME KOMUTU ---
@client.on(events.NewMessage(outgoing=True, pattern=r'\.update'))
async def update_bot(event):
    await event.edit("🔄 **Güncellemeler kontrol ediliyor...**")
    try:
        repo = git.Repo(os.getcwd())
        origin = repo.remotes.origin
        origin.fetch()
        
        # Yeni değişiklik var mı kontrol et
        if repo.head.commit != origin.refs.main.commit:
            await event.edit("📥 **Yeni sürüm bulundu, indiriliyor ve yeniden başlatılıyor...**")
            origin.pull()
            # Botu yeniden başlat (Sisteme bağlı olarak değişebilir)
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await event.edit("✅ **Bot zaten güncel!**")
    except Exception as e:
        await event.edit(f"❌ **Hata:** `{str(e)}` \n(Not: Git kurulumu ve repo bağlantısı gereklidir.)")

# --- MODÜL YÜKLEME SİSTEMİ ---
@client.on(events.NewMessage(outgoing=True, pattern=r'\.pinstall'))
async def pinstall(event):
    if not event.reply_to_msg_id:
        return await event.edit("Lütfen bir `.py` dosyasına yanıt verin!")
    
    reply_msg = await event.get_reply_message()
    if reply_msg.media and reply_msg.file.ext == '.py':
        if not os.path.exists("modules"):
            os.makedirs("modules")
            
        file_path = await reply_msg.download_media(file="modules/")
        mod_name = os.path.basename(file_path).replace('.py', '')
        
        try:
            spec = importlib.util.spec_from_file_location(mod_name, file_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # Modül içindeki event handler'ları client'a ekle
            client.add_event_handler(mod.handler) 
            await event.edit(f"✅ `{mod_name}` modülü başarıyla kuruldu ve aktif edildi!")
        except Exception as e:
            await event.edit(f"❌ Modül yükleme hatası: `{e}`")

# --- TEMEL KOMUTLAR ---
@client.on(events.NewMessage(outgoing=True, pattern=r'\.alive'))
async def alive(event):
    await event.edit("🚀 **Userbot Canlı!**\n\n📌 **Sürüm:** 1.0.0\n🛠 **Durum:** Stabil")

client.run_until_disconnected()
