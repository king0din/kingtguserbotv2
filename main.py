import os
import sys
import asyncio
import importlib.util
import glob
import inspect
import subprocess
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv
import git

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # Örnek: "username/repo"

client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

# Yüklenen modülleri takip et
loaded_modules = {}

def log(text):
    print(f"\033[94m[SİSTEM]\033[0m {text}")

def install_package(package_name):
    """Pip ile paket kur"""
    try:
        log(f"📦 {package_name} kuruluyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])
        log(f"✅ {package_name} kuruldu")
        return True
    except Exception as e:
        log(f"❌ {package_name} kurulamadı: {e}")
        return False

def check_requirements(path):
    """Modül dosyasındaki requirements yorumunu kontrol et"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                # # requires: paket1, paket2 formatını ara
                if line.strip().startswith('# requires:') or line.strip().startswith('# requirements:'):
                    packages = line.split(':', 1)[1].strip().split(',')
                    return [pkg.strip() for pkg in packages if pkg.strip()]
    except:
        pass
    return []

async def load_plugins(plugin_name):
    try:
        path = f"modules/{plugin_name}.py"
        if not os.path.exists(path):
            log(f"❌ {path} bulunamadı")
            return False
        
        # Modül gereksinimlerini kontrol et
        required_packages = check_requirements(path)
        if required_packages:
            log(f"🔍 {plugin_name} için gereksinimler: {', '.join(required_packages)}")
            for pkg in required_packages:
                try:
                    __import__(pkg)
                except ImportError:
                    log(f"⚠️ {pkg} bulunamadı, kuruluyor...")
                    if not install_package(pkg):
                        log(f"❌ {plugin_name} yüklenemedi: {pkg} kurulamadı")
                        return False
        
        # Modülü yükle
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        if spec is None or spec.loader is None:
            log(f"❌ {plugin_name} spec oluşturulamadı")
            return False
            
        mod = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = mod
        
        try:
            spec.loader.exec_module(mod)
        except ImportError as e:
            # Import hatası varsa, eksik paketi bulmaya çalış
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            log(f"⚠️ {plugin_name} için {missing} gerekli, kuruluyor...")
            if install_package(missing):
                # Tekrar dene
                importlib.reload(mod)
            else:
                log(f"❌ {plugin_name} yüklenemedi: {missing} kurulamadı")
                return False
        
        # YÖNTEM 1: register() fonksiyonu var mı kontrol et (ÖNERİLEN)
        if hasattr(mod, 'register') and callable(mod.register):
            mod.register(client)  # Client'ı modüle gönder
            loaded_modules[plugin_name] = mod
            log(f"✅ {plugin_name} yüklendi (register fonksiyonu)")
            return True
        
        # YÖNTEM 2: EventBuilder nesnelerini ara
        count = 0
        for name, obj in inspect.getmembers(mod):
            if not callable(obj) or name.startswith('_'):
                continue
            
            if isinstance(obj, events.common.EventBuilder):
                client.add_event_handler(obj)
                count += 1
                log(f"  ✓ {name} eklendi (EventBuilder)")
        
        if count > 0:
            loaded_modules[plugin_name] = mod
            log(f"✅ {plugin_name} yüklendi ({count} handler)")
            return True
        
        # YÖNTEM 3: __plugin_handlers__ listesi var mı?
        if hasattr(mod, '__plugin_handlers__'):
            for handler in mod.__plugin_handlers__:
                client.add_event_handler(handler)
                count += 1
            if count > 0:
                loaded_modules[plugin_name] = mod
                log(f"✅ {plugin_name} yüklendi ({count} handler)")
                return True
        
        # Hiçbir yöntem çalışmadı
        funcs = [n for n, o in inspect.getmembers(mod) if inspect.iscoroutinefunction(o)]
        log(f"⚠️ {plugin_name} yüklendi ama event handler bulunamadı")
        if funcs:
            log(f"   Bulunan async fonksiyonlar: {', '.join(funcs)}")
            log(f"   💡 İpucu: Modülde register(client) fonksiyonu ekleyin")
        return False
            
    except Exception as e:
        log(f"❌ {plugin_name} yüklenemedi: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- INLINE BOT ---
@bot.on(events.InlineQuery)
async def inline_handler(event):
    if event.text == "help_menu":
        builder = event.builder
        await event.answer([builder.article(
            "Userbot Menü", 
            text="**🤖 Komut Paneli**",
            buttons=[
                [Button.inline("📜 Komutlar", "cmds")],
                [Button.inline("🔌 Modüller", "mods")],
                [Button.inline("❌ Kapat", "close")]
            ]
        )])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    if data == "cmds":
        cmd_text = "**📜 Ana Komutlar:**\n\n"
        cmd_text += "• `.start` - Bot durumunu kontrol et\n"
        cmd_text += "• `.help` - Bu menüyü göster\n"
        cmd_text += "• `.pinstall` - Modül yükle\n"
        cmd_text += "• `.modules` - Yüklü modülleri listele\n"
        cmd_text += "• `.update` - GitHub'dan güncelle\n"
        cmd_text += "• `.hardupdate` - Zorla güncelle\n"
        cmd_text += "• `.gitpull` - Manuel pull\n"
        cmd_text += "• `.restart` - Botu yeniden başlat"
        await event.edit(cmd_text, buttons=[[Button.inline("🔙 Geri", "back")]])
    elif data == "mods":
        if loaded_modules:
            mod_text = "**🔌 Yüklü Modüller:**\n\n"
            mod_text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
        else:
            mod_text = "⚠️ Henüz modül yüklenmemiş"
        await event.edit(mod_text, buttons=[[Button.inline("🔙 Geri", "back")]])
    elif data == "back":
        await event.edit(
            "**🤖 Komut Paneli**",
            buttons=[
                [Button.inline("📜 Komutlar", "cmds")],
                [Button.inline("🔌 Modüller", "mods")],
                [Button.inline("❌ Kapat", "close")]
            ]
        )
    elif data == "close":
        await event.delete()

# --- USERBOT ---
@client.on(events.NewMessage(outgoing=True, pattern=r'^\.start$'))
async def start(e):
    await e.edit("🚀 **Userbot Online!**")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.help$'))
async def help_cmd(e):
    try:
        me = await bot.get_me()
        res = await client.inline_query(me.username, "help_menu")
        await res[0].click(e.chat_id)
        await e.delete()
    except Exception as err:
        await e.edit(f"❌ Hata: {err}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.modules

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())))
async def list_modules(e):
    if loaded_modules:
        text = "**🔌 Yüklü Modüller:**\n\n"
        text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
    else:
        text = "⚠️ Henüz modül yüklenmemiş"
    await e.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.update

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())))
async def update_bot(e):
    """GitHub'dan bot güncellemesi"""
    msg = await e.edit("🔄 **Güncelleme kontrol ediliyor...**")
    
    try:
        # Git repo kontrolü
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!\n\n"
                          "**Manuel Kurulum:**\n"
                          "```bash\n"
                          "git clone https://github.com/USERNAME/REPO .\n"
                          "```")
            return
        
        repo = git.Repo(".")
        
        # Mevcut branch'i al
        current_branch = repo.active_branch.name
        
        # Değişiklikleri kontrol et
        origin = repo.remotes.origin
        origin.fetch()
        
        commits_behind = list(repo.iter_commits(f'{current_branch}..origin/{current_branch}'))
        
        if not commits_behind:
            await msg.edit("✅ **Bot zaten güncel!**\n\n"
                          f"📌 Branch: `{current_branch}`\n"
                          f"🔖 Commit: `{repo.head.commit.hexsha[:7]}`")
            return
        
        # Güncelleme mesajı
        update_info = f"🆕 **{len(commits_behind)} yeni commit bulundu!**\n\n"
        update_info += "**Son Değişiklikler:**\n"
        for i, commit in enumerate(commits_behind[:3], 1):
            update_info += f"{i}. {commit.summary[:50]}\n"
        if len(commits_behind) > 3:
            update_info += f"   _{len(commits_behind) - 3} değişiklik daha..._\n"
        
        update_info += "\n⏳ Güncelleniyor..."
        await msg.edit(update_info)
        
        # Stash local changes
        if repo.is_dirty():
            repo.git.stash('save', 'Auto-stash before update')
            stashed = True
        else:
            stashed = False
        
        # Pull latest changes
        origin.pull(current_branch)
        
        # Stash'i geri al
        if stashed:
            try:
                repo.git.stash('pop')
            except:
                pass
        
        # Requirements güncelle
        if os.path.exists("requirements.txt"):
            await msg.edit("📦 Bağımlılıklar güncelleniyor...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
        
        await msg.edit("✅ **Güncelleme tamamlandı!**\n\n"
                      f"🔖 Yeni Commit: `{repo.head.commit.hexsha[:7]}`\n\n"
                      "🔄 Bot yeniden başlatılıyor...")
        
        await asyncio.sleep(2)
        
        # Botu yeniden başlat
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except git.exc.GitCommandError as e:
        await msg.edit(f"❌ **Git Hatası:**\n```\n{str(e)}\n```\n\n"
                      "💡 `.hardupdate` komutunu deneyin (tüm değişiklikleri siler)")
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.hardupdate

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())))
async def hard_update(e):
    """Zorla güncelleme (tüm local değişiklikleri siler)"""
    msg = await e.edit("⚠️ **HARD UPDATE**\n\n"
                      "Bu işlem tüm local değişiklikleri silecek!\n"
                      "⏳ 5 saniye içinde iptal için mesajı silin...")
    
    await asyncio.sleep(5)
    
    try:
        # Mesaj silinmiş mi kontrol et
        try:
            await msg.edit("🔄 Hard update başlatılıyor...")
        except:
            return  # Mesaj silindi, iptal
        
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!")
            return
        
        repo = git.Repo(".")
        origin = repo.remotes.origin
        current_branch = repo.active_branch.name
        
        # Tüm değişiklikleri sil
        repo.git.reset('--hard', f'origin/{current_branch}')
        repo.git.clean('-fd')
        
        # Pull
        origin.pull(current_branch)
        
        # Requirements güncelle
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
        
        await msg.edit("✅ **Hard update tamamlandı!**\n\n"
                      "🔄 Bot yeniden başlatılıyor...")
        
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.gitpull

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())))
async def git_pull(e):
    """Manuel git pull (yeniden başlatma olmadan)"""
    msg = await e.edit("🔄 Git pull yapılıyor...")
    
    try:
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!")
            return
        
        repo = git.Repo(".")
        origin = repo.remotes.origin
        current_branch = repo.active_branch.name
        
        # Fetch ve pull
        origin.fetch()
        result = origin.pull(current_branch)
        
        if result[0].flags & result[0].HEAD_UPTODATE:
            await msg.edit("✅ Zaten güncel!")
        else:
            await msg.edit(f"✅ Pull tamamlandı!\n\n"
                          f"🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n\n"
                          "⚠️ Değişikliklerin aktif olması için `.restart` kullanın")
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.restart

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())))
async def restart_bot(e):
    """Botu yeniden başlat"""
    await e.edit("🔄 Bot yeniden başlatılıyor...")
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pinstall$'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"):
            os.makedirs("modules")
        
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        
        await e.edit(f"⏳ `{name}` yükleniyor...")
        
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` başarıyla yüklendi ve aktif!")
        else:
            await e.edit(f"⚠️ `{name}` yüklendi ama event handler bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    log("✅ Userbot bağlandı")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    log("✅ Inline bot bağlandı")
    
    # Modüller klasörünü oluştur
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    # Mevcut modülleri yükle
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("✅ Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
