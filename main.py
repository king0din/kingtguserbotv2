import os
import sys
import asyncio
import importlib.util
import glob
import inspect
import subprocess
import time
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv
import git

# ============================================
# BOT SÜRÜM BİLGİSİ
# ============================================
__version__ = "1.0.2"
__author__ = "KingTG"
__repo__ = "github.com/yourusername/kingtguserbotv2"
# ============================================

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

loaded_modules = {}
start_time = time.time()

def log(text):
    print(f"\033[94m[SİSTEM]\033[0m {text}")

def get_readable_time(seconds):
    intervals = (
        ('gün', 86400),
        ('saat', 3600),
        ('dakika', 60),
        ('saniye', 1),
    )
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append(f"{int(value)} {name}")
    return ', '.join(result[:2]) if result else '0 saniye'

def install_package(package_name):
    try:
        log(f"📦 {package_name} kuruluyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])
        log(f"✅ {package_name} kuruldu")
        return True
    except Exception as e:
        log(f"❌ {package_name} kurulamadı: {e}")
        return False

def check_requirements(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
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
        
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        if spec is None or spec.loader is None:
            log(f"❌ {plugin_name} spec oluşturulamadı")
            return False
            
        mod = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = mod
        
        try:
            spec.loader.exec_module(mod)
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            log(f"⚠️ {plugin_name} için {missing} gerekli, kuruluyor...")
            if install_package(missing):
                importlib.reload(mod)
            else:
                log(f"❌ {plugin_name} yüklenemedi: {missing} kurulamadı")
                return False
        
        if hasattr(mod, 'register') and callable(mod.register):
            mod.register(client)
            loaded_modules[plugin_name] = mod
            log(f"✅ {plugin_name} yüklendi (register fonksiyonu)")
            return True
        
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
        
        if hasattr(mod, '__plugin_handlers__'):
            for handler in mod.__plugin_handlers__:
                client.add_event_handler(handler)
                count += 1
            if count > 0:
                loaded_modules[plugin_name] = mod
                log(f"✅ {plugin_name} yüklendi ({count} handler)")
                return True
        
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

@bot.on(events.InlineQuery)
async def inline_handler(event):
    if event.text == "help_menu":
        builder = event.builder
        await event.answer([builder.article(
            "Userbot Menü", 
            text=f"**🤖 Komut Paneli** `v{__version__}`",
            buttons=[
                [Button.inline("📜 Komutlar", b"cmds")],
                [Button.inline("🔌 Modüller", b"mods")],
                [Button.inline("❌ Kapat", b"close")]
            ]
        )])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    
    if data == "cmds":
        cmd_text = f"**📜 Ana Komutlar** `v{__version__}`\n\n"
        cmd_text += "• `.start` - Bot bilgileri\n"
        cmd_text += "• `.ping` - Ping & Uptime\n"
        cmd_text += "• `.help` - Bu menüyü göster\n"
        cmd_text += "• `.pinstall` - Modül yükle\n"
        cmd_text += "• `.delpin <isim>` - Modül sil\n"
        cmd_text += "• `.modules` - Yüklü modüller\n"
        cmd_text += "• `.listpins` - Tüm pluginler\n"
        cmd_text += "• `.update` - GitHub'dan güncelle\n"
        cmd_text += "• `.hardupdate` - Zorla güncelle\n"
        cmd_text += "• `.gitpull` - Manuel pull\n"
        cmd_text += "• `.restart` - Yeniden başlat"
        await event.edit(cmd_text, buttons=[[Button.inline("🔙 Geri", b"back")]])
    
    elif data == "mods":
        if loaded_modules:
            mod_text = "**🔌 Yüklü Modüller:**\n\n"
            mod_text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
            mod_text += f"\n\n**Toplam:** {len(loaded_modules)} modül"
        else:
            mod_text = "⚠️ Henüz modül yüklenmemiş"
        await event.edit(mod_text, buttons=[[Button.inline("🔙 Geri", b"back")]])
    
    elif data == "back":
        await event.edit(
            f"**🤖 Komut Paneli** `v{__version__}`",
            buttons=[
                [Button.inline("📜 Komutlar", b"cmds")],
                [Button.inline("🔌 Modüller", b"mods")],
                [Button.inline("❌ Kapat", b"close")]
            ]
        )
    
    elif data == "close":
        await event.delete()

@client.on(events.CallbackQuery)
async def userbot_callback_handler(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    
    if data == "update":
        await event.edit("🔄 **Güncelleme kontrol ediliyor...**")
        
        try:
            if not os.path.exists(".git"):
                await event.edit("❌ Bu bir git repository değil!")
                return
            
            repo = git.Repo(".")
            current_branch = repo.active_branch.name
            origin = repo.remotes.origin
            origin.fetch()
            
            commits_behind = list(repo.iter_commits(f'{current_branch}..origin/{current_branch}'))
            
            if not commits_behind:
                await event.answer("✅ Bot zaten güncel!", alert=True)
                return
            
            buttons = [
                [Button.inline("✅ Güncelle", b"update_confirm"), Button.inline("❌ İptal", b"update_cancel")]
            ]
            
            update_info = f"🆕 **{len(commits_behind)} yeni commit bulundu!**\n\n"
            update_info += "**Son Değişiklikler:**\n"
            for i, commit in enumerate(commits_behind[:3], 1):
                update_info += f"{i}. {commit.summary[:50]}\n"
            if len(commits_behind) > 3:
                update_info += f"   _{len(commits_behind) - 3} değişiklik daha..._\n"
            
            await event.edit(update_info, buttons=buttons)
            
        except Exception as e:
            await event.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")
    
    elif data == "update_confirm":
        await event.edit("⏳ Güncelleniyor...")
        
        try:
            repo = git.Repo(".")
            current_branch = repo.active_branch.name
            origin = repo.remotes.origin
            
            if repo.is_dirty():
                repo.git.stash('save', 'Auto-stash before update')
            
            origin.pull(current_branch)
            
            if os.path.exists("requirements.txt"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
            
            try:
                with open("main.py", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("__version__"):
                            new_version = line.split("=")[1].strip().strip('"').strip("'")
                            break
                    else:
                        new_version = "bilinmiyor"
            except:
                new_version = "bilinmiyor"
            
            await event.edit(f"✅ **Güncelleme tamamlandı!**\n\n🔢 Eski: `v{__version__}`\n🆕 Yeni: `v{new_version}`\n\n🔄 Yeniden başlatılıyor...")
            await asyncio.sleep(2)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            await event.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")
    
    elif data == "update_cancel":
        await event.edit("❌ Güncelleme iptal edildi.")
        await asyncio.sleep(2)
        await event.delete()
    
    elif data == "show_modules":
        if loaded_modules:
            text = "**🔌 Yüklü Modüller:**\n\n"
            text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
            text += f"\n\n**Toplam:** {len(loaded_modules)} modül"
        else:
            text = "⚠️ Henüz modül yüklenmemiş"
        
        buttons = [[Button.inline("🔙 Ana Menü", b"back_to_start")]]
        await event.edit(text, buttons=buttons)
    
    elif data == "ping":
        start_time_ping = time.time()
        await event.answer("Ping hesaplanıyor...")
        end_time_ping = time.time()
        ping = (end_time_ping - start_time_ping) * 1000
        
        uptime = get_readable_time(time.time() - start_time)
        
        text = f"**🏓 Pong!**\n\n"
        text += f"**⚡ Ping:** `{ping:.2f}ms`\n"
        text += f"**⏱️ Uptime:** `{uptime}`\n"
        text += f"**🔢 Sürüm:** `v{__version__}`"
        
        buttons = [[Button.inline("🔙 Ana Menü", b"back_to_start")]]
        await event.edit(text, buttons=buttons)
    
    elif data == "help_main":
        text = f"**🤖 Komut Paneli** `v{__version__}`"
        buttons = [
            [Button.inline("📜 Komutlar", b"help_cmds")],
            [Button.inline("🔌 Modüller", b"help_mods")],
            [Button.inline("🔙 Ana Menü", b"back_to_start")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data == "help_cmds":
        cmd_text = f"**📜 Ana Komutlar** `v{__version__}`\n\n"
        cmd_text += "• `.start` - Bot bilgileri\n"
        cmd_text += "• `.ping` - Ping & Uptime\n"
        cmd_text += "• `.help` - Yardım menüsü\n"
        cmd_text += "• `.pinstall` - Modül yükle\n"
        cmd_text += "• `.delpin <isim>` - Modül sil\n"
        cmd_text += "• `.modules` - Yüklü modüller\n"
        cmd_text += "• `.listpins` - Tüm pluginler\n"
        cmd_text += "• `.update` - GitHub'dan güncelle\n"
        cmd_text += "• `.hardupdate` - Zorla güncelle\n"
        cmd_text += "• `.gitpull` - Manuel pull\n"
        cmd_text += "• `.restart` - Yeniden başlat"
        
        buttons = [[Button.inline("🔙 Geri", b"help_main")]]
        await event.edit(cmd_text, buttons=buttons)
    
    elif data == "help_mods":
        if loaded_modules:
            mod_text = "**🔌 Yüklü Modüller:**\n\n"
            mod_text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
            mod_text += f"\n\n**Toplam:** {len(loaded_modules)} modül"
        else:
            mod_text = "⚠️ Henüz modül yüklenmemiş"
        
        buttons = [[Button.inline("🔙 Geri", b"help_main")]]
        await event.edit(mod_text, buttons=buttons)
    
    elif data == "back_to_start":
        uptime = get_readable_time(time.time() - start_time)
        me = await client.get_me()
        
        text = f"**🤖 KingTG UserBot**\n\n"
        text += f"**👤 Kullanıcı:** `{me.first_name}`\n"
        text += f"**📱 Telefon:** `+{me.phone}`\n"
        text += f"**🆔 ID:** `{me.id}`\n"
        text += f"**📍 Username:** @{me.username}\n\n"
        text += f"**🔢 Sürüm:** `v{__version__}`\n"
        text += f"**⏱️ Uptime:** `{uptime}`\n"
        text += f"**🔌 Modüller:** `{len(loaded_modules)}`\n"
        text += f"**🐍 Python:** `{sys.version.split()[0]}`\n\n"
        text += f"**💻 Repo:** `{__repo__}`\n"
        text += f"**👨‍💻 Geliştirici:** `{__author__}`"
        
        buttons = [
            [Button.inline("🔄 Güncelle", b"update"), Button.inline("🔌 Modüller", b"show_modules")],
            [Button.inline("🏓 Ping", b"ping"), Button.inline("❓ Yardım", b"help_main")],
            [Button.inline("🔁 Yeniden Başlat", b"restart_confirm")]
        ]
        
        await event.edit(text, buttons=buttons)
    
    elif data == "restart_confirm":
        buttons = [
            [Button.inline("✅ Evet", b"restart_yes"), Button.inline("❌ Hayır", b"restart_no")]
        ]
        await event.edit("⚠️ **Botu yeniden başlatmak istediğinize emin misiniz?**", buttons=buttons)
    
    elif data == "restart_yes":
        await event.edit("🔄 Bot yeniden başlatılıyor...")
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    elif data == "restart_no":
        await event.answer("❌ İptal edildi", alert=False)
        await event.delete()

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.start$'))
async def start(e):
    uptime = get_readable_time(time.time() - start_time)
    me = await client.get_me()
    
    text = f"**🤖 KingTG UserBot**\n\n"
    text += f"**👤 Kullanıcı:** `{me.first_name}`\n"
    text += f"**📱 Telefon:** `+{me.phone}`\n"
    text += f"**🆔 ID:** `{me.id}`\n"
    text += f"**📍 Username:** @{me.username}\n\n"
    text += f"**🔢 Sürüm:** `v{__version__}`\n"
    text += f"**⏱️ Uptime:** `{uptime}`\n"
    text += f"**🔌 Modüller:** `{len(loaded_modules)}`\n"
    text += f"**🐍 Python:** `{sys.version.split()[0]}`\n\n"
    text += f"**💻 Repo:** `{__repo__}`\n"
    text += f"**👨‍💻 Geliştirici:** `{__author__}`"
    
    buttons = [
        [Button.inline("🔄 Güncelle", b"update"), Button.inline("🔌 Modüller", b"show_modules")],
        [Button.inline("🏓 Ping", b"ping"), Button.inline("❓ Yardım", b"help_main")],
        [Button.inline("🔁 Yeniden Başlat", b"restart_confirm")]
    ]
    
    await e.reply(text, buttons=buttons)
    await e.delete()

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.ping$'))
async def ping_cmd(e):
    start = time.time()
    msg = await e.edit("🏓 **Pong!**")
    end = time.time()
    ping = (end - start) * 1000
    
    uptime = get_readable_time(time.time() - start_time)
    
    text = f"**🏓 Pong!**\n\n"
    text += f"**⚡ Ping:** `{ping:.2f}ms`\n"
    text += f"**⏱️ Uptime:** `{uptime}`\n"
    text += f"**🔢 Sürüm:** `v{__version__}`"
    
    await msg.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.help$'))
async def help_cmd(e):
    try:
        me = await bot.get_me()
        res = await client.inline_query(me.username, "help_menu")
        await res[0].click(e.chat_id)
        await e.delete()
    except Exception as err:
        await e.edit(f"❌ Hata: {err}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.modules$'))
async def list_modules(e):
    if loaded_modules:
        text = "**🔌 Yüklü Modüller:**\n\n"
        text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
    else:
        text = "⚠️ Henüz modül yüklenmemiş"
    await e.edit(text)

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

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.delpin (\S+)$'))
async def delpin(e):
    plugin_name = e.pattern_match.group(1)
    
    if plugin_name.endswith('.py'):
        plugin_name = plugin_name[:-3]
    
    path = f"modules/{plugin_name}.py"
    
    if not os.path.exists(path):
        await e.edit(f"❌ `{plugin_name}` bulunamadı!\n\n💡 Yüklü modüller için `.modules` kullanın.")
        return
    
    await e.edit(f"⏳ `{plugin_name}` siliniyor...")
    
    try:
        os.remove(path)
        
        if plugin_name in loaded_modules:
            del loaded_modules[plugin_name]
        
        if plugin_name in sys.modules:
            del sys.modules[plugin_name]
        
        await e.edit(f"✅ `{plugin_name}` başarıyla silindi!\n\n🔄 Event handler'lar yeniden başlatma sonrası temizlenecek.")
        
    except Exception as err:
        await e.edit(f"❌ `{plugin_name}` silinirken hata:\n```\n{str(err)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.listpins$'))
async def listpins(e):
    module_files = glob.glob("modules/*.py")
    
    if not module_files:
        await e.edit("⚠️ `modules/` klasöründe plugin bulunamadı.")
        return
    
    text = "**📦 Dosya Sistemindeki Pluginler:**\n\n"
    
    for f in sorted(module_files):
        name = os.path.basename(f).replace('.py', '')
        size = os.path.getsize(f) / 1024
        status = "✅" if name in loaded_modules else "❌"
        text += f"{status} `{name}` ({size:.1f} KB)\n"
    
    text += f"\n**Toplam:** {len(module_files)} plugin"
    text += f"\n**Yüklü:** {len(loaded_modules)} plugin"
    
    await e.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.update$'))
async def update_bot(e):
    msg = await e.edit("🔄 **Güncelleme kontrol ediliyor...**")
    
    try:
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!\n\n**Manuel Kurulum:**\n```bash\ngit clone https://github.com/USERNAME/REPO .\n```")
            return
        
        repo = git.Repo(".")
        current_branch = repo.active_branch.name
        origin = repo.remotes.origin
        origin.fetch()
        
        commits_behind = list(repo.iter_commits(f'{current_branch}..origin/{current_branch}'))
        
        if not commits_behind:
            await msg.edit(f"✅ **Bot zaten güncel!**\n\n📌 Branch: `{current_branch}`\n🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n🔢 Sürüm: `v{__version__}`")
            return
        
        update_info = f"🆕 **{len(commits_behind)} yeni commit bulundu!**\n\n**Son Değişiklikler:**\n"
        for i, commit in enumerate(commits_behind[:3], 1):
            update_info += f"{i}. {commit.summary[:50]}\n"
        if len(commits_behind) > 3:
            update_info += f"   _{len(commits_behind) - 3} değişiklik daha..._\n"
        
        update_info += "\n⏳ Güncelleniyor..."
        await msg.edit(update_info)
        
        if repo.is_dirty():
            repo.git.stash('save', 'Auto-stash before update')
            stashed = True
        else:
            stashed = False
        
        origin.pull(current_branch)
        
        if stashed:
            try:
                repo.git.stash('pop')
            except:
                pass
        
        if os.path.exists("requirements.txt"):
            await msg.edit("📦 Bağımlılıklar güncelleniyor...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
        
        try:
            with open("main.py", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("__version__"):
                        new_version = line.split("=")[1].strip().strip('"').strip("'")
                        break
                else:
                    new_version = "bilinmiyor"
        except:
            new_version = "bilinmiyor"
        
        await msg.edit(f"✅ **Güncelleme tamamlandı!**\n\n🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n🔢 Eski Sürüm: `v{__version__}`\n🆕 Yeni Sürüm: `v{new_version}`\n\n🔄 Bot yeniden başlatılıyor...")
        
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except git.exc.GitCommandError as e:
        await msg.edit(f"❌ **Git Hatası:**\n```\n{str(e)}\n```\n\n💡 `.hardupdate` komutunu deneyin")
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.hardupdate$'))
async def hard_update(e):
    msg = await e.edit("⚠️ **HARD UPDATE**\n\nBu işlem tüm local değişiklikleri silecek!\n⏳ 5 saniye içinde iptal için mesajı silin...")
    
    await asyncio.sleep(5)
    
    try:
        try:
            await msg.edit("🔄 Hard update başlatılıyor...")
        except:
            return
        
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!")
            return
        
        repo = git.Repo(".")
        origin = repo.remotes.origin
        current_branch = repo.active_branch.name
        
        repo.git.reset('--hard', f'origin/{current_branch}')
        repo.git.clean('-fd')
        origin.pull(current_branch)
        
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
        
        await msg.edit("✅ **Hard update tamamlandı!**\n\n🔄 Bot yeniden başlatılıyor...")
        
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.gitpull$'))
async def git_pull(e):
    msg = await e.edit("🔄 Git pull yapılıyor...")
    
    try:
        if not os.path.exists(".git"):
            await msg.edit("❌ Bu bir git repository değil!")
            return
        
        repo = git.Repo(".")
        origin = repo.remotes.origin
        current_branch = repo.active_branch.name
        
        origin.fetch()
        result = origin.pull(current_branch)
        
        if result[0].flags & result[0].HEAD_UPTODATE:
            await msg.edit("✅ Zaten güncel!")
        else:
            await msg.edit(f"✅ Pull tamamlandı!\n\n🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n\n⚠️ Değişikliklerin aktif olması için `.restart` kullanın")
    except Exception as e:
        await msg.edit(f"❌ **Hata:**\n```\n{str(e)}\n```")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.restart$'))
async def restart_bot(e):
    await e.edit("🔄 Bot yeniden başlatılıyor...")
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def main():
    log("=" * 50)
    log(f"🤖 KingTG UserBot v{__version__}")
    log(f"👨‍💻 Geliştirici: {__author__}")
    log(f"💻 Repo: {__repo__}")
    log("=" * 50)
    
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    me = await client.get_me()
    log(f"✅ Userbot bağlandı: {me.first_name} (@{me.username})")
    
    log("🔄 Inline bot başlatılıyor...")
    await bot.start(bot_token=BOT_TOKEN)
    bot_me = await bot.get_me()
    log(f"✅ Inline bot bağlandı: @{bot_me.username}")
    
    if not os.path.exists("modules"):
        os.makedirs("modules")
        log("📁 modules/ klasörü oluşturuldu")
    
    log("🔄 Modüller yükleniyor...")
    module_files = glob.glob("modules/*.py")
    if module_files:
        for f in module_files:
            name = os.path.basename(f).replace('.py', '')
            await load_plugins(name)
    else:
        log("⚠️ modules/ klasöründe modül bulunamadı")
    
    log("=" * 50)
    log(f"✅ Bot Hazır! Sürüm: v{__version__}")
    log(f"🔌 Yüklü Modüller: {len(loaded_modules)}")
    log(f"📱 Komutlar için .help yazın")
    log("=" * 50)
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
