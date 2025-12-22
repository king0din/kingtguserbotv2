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
__version__ = "1.0.5"
__author__ = "@KingOdi"
__repo__ = "şuanlık özeldir"
# ============================================

load_dotenv()

# ============================================
# ESKİ USERBOT UYUMLULUK KATMANI
# ============================================
def setup_compatibility():
    """Eski userbot pluginleri için uyumluluk katmanı oluştur"""
    
    # userbot klasörünü oluştur
    if not os.path.exists("userbot"):
        os.makedirs("userbot")
        log("📁 userbot/ uyumluluk klasörü oluşturuldu")
    
    # __init__.py - Ana modül değişkenleri
    init_content = '''# KingTG UserBot - Uyumluluk Katmanı
# SedUserBot, AsenaUserBot vb. pluginleri destekler

# Eski pluginlerin kullandığı global değişkenler
CMD_HELP = {}
CMD_LIST = {}
SUDO_LIST = []
BLACKLIST = []
LOGS = None
COUNT_MSG = 0
USERS = {}
BRAIN_CHECKER = []
ZALG_LIST = [
    "̖", "̗", "̘", "̙", "̜", "̝", "̞", "̟", "̠", "̤", "̥", "̦", "̩", "̪", "̫", "̬", "̭", "̮", "̯", "̰", "̱", "̲", "̳", "̹", "̺", "̻", "̼", "ͅ", "͇", "͈", "͉", "͍", "͎", "͓", "͔", "͕", "͖", "͙", "͚", "̣",
    "̕", "̛", "̀", "́", "͘", "̡", "̢", "̧", "̨", "̴", "̵", "̶", "͏", "͜", "͝", "͞", "͟", "͠", "͢", "̸", "̷", "͡", "҉",
    "̍", "̎", "̄", "̅", "̿", "̑", "̆", "̐", "͒", "͗", "͑", "̇", "̈", "̊", "͂", "̓", "̈́", "͊", "͋", "͌", "̃", "̂", "̌", "͐", "̀", "́", "̋", "̏", "̽", "̉", "ͣ", "ͤ", "ͥ", "ͦ", "ͧ", "ͨ", "ͩ", "ͪ", "ͫ", "ͬ", "ͭ", "ͮ", "ͯ", "̾", "͛", "͆", "̚"
]

# Bot bilgileri
bot = None
tgbot = None
'''
    with open("userbot/__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)
    
    # events.py - @register decorator
    events_content = '''# KingTG UserBot - Events Uyumluluk Modülü
from telethon import events
import functools

_client = None
_pending_handlers = []

def set_client(client):
    global _client
    _client = client
    for handler, event in _pending_handlers:
        _client.add_event_handler(handler, event)
    _pending_handlers.clear()

def register(outgoing=True, incoming=False, pattern=None, **kwargs):
    def decorator(func):
        event = events.NewMessage(
            outgoing=outgoing,
            incoming=incoming,
            pattern=pattern,
            **kwargs
        )
        
        @functools.wraps(func)
        async def wrapper(event):
            return await func(event)
        
        if _client is not None:
            _client.add_event_handler(wrapper, event)
        else:
            _pending_handlers.append((wrapper, event))
        
        return wrapper
    return decorator

def on(event):
    def decorator(func):
        if _client is not None:
            _client.add_event_handler(func, event)
        else:
            _pending_handlers.append((func, event))
        return func
    return decorator
'''
    with open("userbot/events.py", "w", encoding="utf-8") as f:
        f.write(events_content)
    
    # cmdhelp.py - CmdHelp sınıfı
    cmdhelp_content = '''# KingTG UserBot - CmdHelp Uyumluluk Modülü
_help_dict = {}

class CmdHelp:
    def __init__(self, module_name):
        self.module_name = module_name
        self.commands = []
        self.info = None
    
    def add_command(self, command, params=None, description=None, example=None):
        self.commands.append({
            'command': command,
            'params': params,
            'description': description,
            'example': example
        })
        return self
    
    def add_info(self, info):
        self.info = info
        return self
    
    def add(self):
        _help_dict[self.module_name] = {
            'commands': self.commands,
            'info': self.info
        }
        return self

def get_all_help():
    return _help_dict

def get_help(module_name):
    return _help_dict.get(module_name)

def format_help(module_name):
    help_data = get_help(module_name)
    if not help_data:
        return None
    
    text = f"**📖 {module_name} Yardım**\\n\\n"
    
    for cmd in help_data['commands']:
        text += f"• `.{cmd['command']}`"
        if cmd['params']:
            text += f" `{cmd['params']}`"
        text += "\\n"
        if cmd['description']:
            text += f"  ➥ {cmd['description']}\\n"
        if cmd['example']:
            text += f"  📝 Örnek: `{cmd['example']}`\\n"
        text += "\\n"
    
    if help_data['info']:
        text += f"ℹ️ {help_data['info']}"
    
    return text
'''
    with open("userbot/cmdhelp.py", "w", encoding="utf-8") as f:
        f.write(cmdhelp_content)
    
    # utils.py - Yardımcı fonksiyonlar
    utils_content = '''# KingTG UserBot - Utils Uyumluluk Modülü
import asyncio
import subprocess

async def edit_or_reply(event, text, **kwargs):
    try:
        return await event.edit(text, **kwargs)
    except:
        return await event.reply(text, **kwargs)

async def edit_delete(event, text, time=5):
    msg = await event.edit(text)
    await asyncio.sleep(time)
    await msg.delete()

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)

async def run_command_async(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode() or stderr.decode()

TEMP_DIR = "/tmp"
CMD_HELP = {}
CMD_LIST = {}
SUDO_LIST = []
BLACKLIST = []
'''
    with open("userbot/utils.py", "w", encoding="utf-8") as f:
        f.write(utils_content)
    
    log("✅ Uyumluluk katmanı hazır (CMD_HELP, ZALG_LIST, events, cmdhelp, utils)")

# ============================================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

loaded_modules = {}
start_time = time.time()

# Restart sonrası mesaj göndermek için
RESTART_FILE = ".restart_info"

def log(text):
    print(f"\033[94m[SİSTEM]\033[0m {text}")

def get_readable_time(seconds):
    """Saniyeyi okunabilir formata çevir"""
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
        
        # Uyumluluk katmanının yüklendiğinden emin ol
        try:
            import userbot
        except ImportError:
            setup_compatibility()
            import userbot
        
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        if spec is None or spec.loader is None:
            log(f"❌ {plugin_name} spec oluşturulamadı")
            return False
            
        mod = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = mod
        
        try:
            spec.loader.exec_module(mod)
        except ImportError as e:
            error_msg = str(e)
            # userbot modülünden import hatası
            if "userbot" in error_msg:
                log(f"⚠️ {plugin_name} userbot uyumluluk hatası: {error_msg}")
                log(f"   💡 Bu plugin tam uyumlu olmayabilir")
                return False
            
            # Diğer eksik paketler
            missing = error_msg.split("'")[1] if "'" in error_msg else error_msg
            log(f"⚠️ {plugin_name} için {missing} gerekli, kuruluyor...")
            if install_package(missing):
                # Modülü tekrar yükle
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, path)
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[plugin_name] = mod
                    spec.loader.exec_module(mod)
                except Exception as retry_err:
                    log(f"❌ {plugin_name} yeniden yüklenemedi: {retry_err}")
                    return False
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
        
        # Eski userbot pluginleri için: @register ile kaydedilenler
        # pending_handlers'a eklenmişlerdir, onları kontrol et
        try:
            from userbot.events import _pending_handlers
            if _pending_handlers:
                for handler, event in _pending_handlers:
                    client.add_event_handler(handler, event)
                    count += 1
                _pending_handlers.clear()
                if count > 0:
                    loaded_modules[plugin_name] = mod
                    log(f"✅ {plugin_name} yüklendi ({count} eski format handler)")
                    return True
        except:
            pass
        
        # Bot handler'ları için register_bot fonksiyonu kontrol et
        if hasattr(mod, 'register_bot') and callable(mod.register_bot):
            try:
                mod.register_bot(bot, client)
                log(f"  ✓ {plugin_name} bot handler'ları yüklendi")
                if plugin_name not in loaded_modules:
                    loaded_modules[plugin_name] = mod
                    count += 1
            except Exception as bot_err:
                log(f"  ⚠️ {plugin_name} bot handler hatası: {bot_err}")
        
        if count > 0:
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

def save_restart_info(chat_id, message_id):
    """Restart bilgisini kaydet"""
    with open(RESTART_FILE, "w") as f:
        f.write(f"{chat_id}|{message_id}")

def get_restart_info():
    """Restart bilgisini oku ve sil"""
    if os.path.exists(RESTART_FILE):
        with open(RESTART_FILE, "r") as f:
            data = f.read().strip()
        os.remove(RESTART_FILE)
        if "|" in data:
            chat_id, msg_id = data.split("|")
            return int(chat_id), int(msg_id)
    return None, None

@bot.on(events.InlineQuery)
async def inline_handler(event):
    builder = event.builder
    
    if event.text == "help_menu":
        await event.answer([builder.article(
            "Userbot Menü", 
            text=f"**🤖 Komut Paneli** `v{__version__}`",
            buttons=[
                [Button.inline("📜 Komutlar", "cmds")],
                [Button.inline("🔌 Modüller", "mods")],
                [Button.inline("❌ Kapat", "close")]
            ]
        )])
    
    elif event.text == "start_menu":
        uptime = get_readable_time(time.time() - start_time)
        me = await client.get_me()
        
        text = f"**🤖 KingTG UserBot**\n\n"
        text += f"**👤 Kullanıcı:** `{me.first_name}`\n"
        text += f"**🆔 ID:** `{me.id}`\n"
        text += f"**📍 Username:** @{me.username}\n\n"
        text += f"**🔢 Sürüm:** `v{__version__}`\n"
        text += f"**⏱️ Uptime:** `{uptime}`\n"
        text += f"**🔌 Modüller:** `{len(loaded_modules)}`\n"
        text += f"**🐍 Python:** `{sys.version.split()[0]}`\n\n"
        text += f"**💻 Repo:** `{__repo__}`\n"
        text += f"**👨‍💻 Geliştirici:** `{__author__}`"
        
        await event.answer([builder.article(
            "Userbot Start", 
            text=text,
            buttons=[
                [Button.inline("📜 Yardım", "help"), Button.inline("🔄 Güncelle", "update")],
                [Button.inline("⚠️ Hard Update", "hard_update")],
                [Button.inline("🔌 Modüller", "mods"), Button.inline("🔃 Restart", "restart")],
                [Button.inline("❌ Kapat", "close")]
            ]
        )])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    
    if data == "cmds" or data == "help":
        cmd_text = f"**📜 Ana Komutlar** `v{__version__}`\n\n"
        cmd_text += "• `.start` - Bot bilgileri\n"
        cmd_text += "• `.ping` - Ping & Uptime\n"
        cmd_text += "• `.help` - Bu menüyü göster\n"
        cmd_text += "• `.pinstall` - Modül yükle\n"
        cmd_text += "• `.delpin <isim>` - Modül sil\n"
        cmd_text += "• `.modules` - Yüklü modüller\n"
        cmd_text += "• `.listpins` - Tüm pluginler\n"
        cmd_text += "• `.pluginhelp` - Plugin yardımları\n"
        cmd_text += "• `.update` - GitHub'dan güncelle\n"
        cmd_text += "• `.hardupdate` - Zorla güncelle\n"
        cmd_text += "• `.gitpull` - Manuel pull\n"
        cmd_text += "• `.restart` - Yeniden başlat"
        await event.edit(cmd_text, buttons=[[Button.inline("🔙 Geri", "back_start")]])
    
    elif data == "mods":
        if loaded_modules:
            mod_text = "**🔌 Yüklü Modüller:**\n\n"
            mod_text += "\n".join([f"• `{name}`" for name in loaded_modules.keys()])
            mod_text += f"\n\n**Toplam:** {len(loaded_modules)} modül"
        else:
            mod_text = "⚠️ Henüz modül yüklenmemiş"
        await event.edit(mod_text, buttons=[[Button.inline("🔙 Geri", "back_start")]])
    
    elif data == "back" or data == "back_start":
        uptime = get_readable_time(time.time() - start_time)
        me = await client.get_me()
        
        text = f"**🤖 KingTG UserBot**\n\n"
        text += f"**👤 Kullanıcı:** `{me.first_name}`\n"
        text += f"**🆔 ID:** `{me.id}`\n"
        text += f"**📍 Username:** @{me.username}\n\n"
        text += f"**🔢 Sürüm:** `v{__version__}`\n"
        text += f"**⏱️ Uptime:** `{uptime}`\n"
        text += f"**🔌 Modüller:** `{len(loaded_modules)}`\n"
        text += f"**🐍 Python:** `{sys.version.split()[0]}`\n\n"
        text += f"**💻 Repo:** `{__repo__}`\n"
        text += f"**👨‍💻 Geliştirici:** `{__author__}`"
        
        await event.edit(
            text,
            buttons=[
                [Button.inline("📜 Yardım", "help"), Button.inline("🔄 Güncelle", "update")],
                [Button.inline("⚠️ Hard Update", "hard_update")],
                [Button.inline("🔌 Modüller", "mods"), Button.inline("🔃 Restart", "restart")],
                [Button.inline("❌ Kapat", "close")]
            ]
        )
    
    elif data == "update":
        await event.edit("🔄 **Güncelleme kontrol ediliyor...**")
        
        try:
            if not os.path.exists(".git"):
                await event.edit("❌ Bu bir git repository değil!\n\n**Manuel Kurulum:**\n```bash\ngit clone https://github.com/USERNAME/REPO .\n```",
                    buttons=[[Button.inline("🔙 Geri", "back_start")]])
                return
            
            repo = git.Repo(".")
            current_branch = repo.active_branch.name
            origin = repo.remotes.origin
            origin.fetch()
            
            commits_behind = list(repo.iter_commits(f'{current_branch}..origin/{current_branch}'))
            
            if not commits_behind:
                await event.edit(f"✅ **Bot zaten güncel!**\n\n📌 Branch: `{current_branch}`\n🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n🔢 Sürüm: `v{__version__}`",
                    buttons=[[Button.inline("🔙 Geri", "back_start")]])
                return
            
            update_info = f"🆕 **{len(commits_behind)} yeni commit bulundu!**\n\n**Son Değişiklikler:**\n"
            for i, commit in enumerate(commits_behind[:3], 1):
                update_info += f"{i}. {commit.summary[:50]}\n"
            if len(commits_behind) > 3:
                update_info += f"   _{len(commits_behind) - 3} değişiklik daha..._\n"
            
            update_info += "\n⏳ Güncelleniyor..."
            await event.edit(update_info)
            
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
                await event.edit("📦 Bağımlılıklar güncelleniyor...")
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
            
            await event.edit(f"✅ **Güncelleme tamamlandı!**\n\n🔖 Commit: `{repo.head.commit.hexsha[:7]}`\n🔢 Eski Sürüm: `v{__version__}`\n🆕 Yeni Sürüm: `v{new_version}`\n\n🔄 Bot yeniden başlatılıyor...")
            
            # Restart bilgisini kaydet
            save_restart_info(event.chat_id, event.message_id)
            
            await asyncio.sleep(2)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except git.exc.GitCommandError as e:
            await event.edit(f"❌ **Git Hatası:**\n```\n{str(e)}\n```\n\n💡 Hard Update butonunu deneyin",
                buttons=[[Button.inline("⚠️ Hard Update", "hard_update"), Button.inline("🔙 Geri", "back_start")]])
        except Exception as e:
            await event.edit(f"❌ **Hata:**\n```\n{str(e)}\n```",
                buttons=[[Button.inline("🔙 Geri", "back_start")]])
    
    elif data == "hard_update":
        await event.edit("⚠️ **HARD UPDATE**\n\nBu işlem tüm local değişiklikleri silecek!\n\nDevam etmek istiyor musunuz?",
            buttons=[
                [Button.inline("✅ Evet, Devam Et", "hard_update_confirm")],
                [Button.inline("❌ İptal", "back_start")]
            ])
    
    elif data == "hard_update_confirm":
        try:
            await event.edit("🔄 Hard update başlatılıyor...")
            
            if not os.path.exists(".git"):
                await event.edit("❌ Bu bir git repository değil!",
                    buttons=[[Button.inline("🔙 Geri", "back_start")]])
                return
            
            repo = git.Repo(".")
            origin = repo.remotes.origin
            current_branch = repo.active_branch.name
            
            repo.git.reset('--hard', f'origin/{current_branch}')
            repo.git.clean('-fd')
            origin.pull(current_branch)
            
            if os.path.exists("requirements.txt"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--upgrade"])
            
            await event.edit("✅ **Hard update tamamlandı!**\n\n🔄 Bot yeniden başlatılıyor...")
            
            # Restart bilgisini kaydet
            save_restart_info(event.chat_id, event.message_id)
            
            await asyncio.sleep(2)
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        except Exception as e:
            await event.edit(f"❌ **Hata:**\n```\n{str(e)}\n```",
                buttons=[[Button.inline("🔙 Geri", "back_start")]])
    
    elif data == "restart":
        await event.edit("🔄 Bot yeniden başlatılıyor...")
        
        # Restart bilgisini kaydet
        save_restart_info(event.chat_id, event.message_id)
        
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    elif data == "close":
        # Inline mesajlar silinemez, bunun yerine düzenle
        try:
            await event.edit("❌ **Menü kapatıldı.**\n\n💡 Tekrar açmak için `.start` yazın.")
        except:
            await event.answer("Menü kapatıldı!", alert=True)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.start$'))
async def start(e):
    try:
        me_bot = await bot.get_me()
        res = await client.inline_query(me_bot.username, "start_menu")
        await res[0].click(e.chat_id)
        await e.delete()
    except Exception as err:
        # Fallback: Inline bot çalışmazsa eski yöntem
        uptime = get_readable_time(time.time() - start_time)
        me = await client.get_me()
        
        text = f"**🤖 KingTG UserBot**\n\n"
        text += f"**👤 Kullanıcı:** `{me.first_name}`\n"
        text += f"**🆔 ID:** `{me.id}`\n"
        text += f"**📍 Username:** @{me.username}\n\n"
        text += f"**🔢 Sürüm:** `v{__version__}`\n"
        text += f"**⏱️ Uptime:** `{uptime}`\n"
        text += f"**🔌 Modüller:** `{len(loaded_modules)}`\n"
        text += f"**🐍 Python:** `{sys.version.split()[0]}`\n\n"
        text += f"**💻 Repo:** `{__repo__}`\n"
        text += f"**👨‍💻 Geliştirici:** `{__author__}`\n\n"
        text += f"⚠️ Inline bot hatası: {err}"
        
        await e.edit(text)

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

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.pluginhelp(?:\s+(\S+))?$'))
async def plugin_help(e):
    """Plugin yardımlarını göster"""
    try:
        from userbot.cmdhelp import get_all_help, format_help
        
        plugin_name = e.pattern_match.group(1)
        
        if plugin_name:
            # Belirli plugin yardımı
            help_text = format_help(plugin_name)
            if help_text:
                await e.edit(help_text)
            else:
                await e.edit(f"❌ `{plugin_name}` için yardım bulunamadı.")
        else:
            # Tüm plugin yardımları
            all_help = get_all_help()
            if all_help:
                text = "**📚 Plugin Yardımları**\n\n"
                for name in sorted(all_help.keys()):
                    cmd_count = len(all_help[name]['commands'])
                    text += f"• `{name}` ({cmd_count} komut)\n"
                text += f"\n**Toplam:** {len(all_help)} plugin\n"
                text += "\n💡 Detay için: `.pluginhelp <plugin_adı>`"
                await e.edit(text)
            else:
                await e.edit("⚠️ Henüz yardım kaydı olan plugin yok.")
    except Exception as err:
        await e.edit(f"❌ Hata: {err}")

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
        
        # Restart bilgisini kaydet
        save_restart_info(e.chat_id, msg.id)
        
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
        
        # Restart bilgisini kaydet
        save_restart_info(e.chat_id, msg.id)
        
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
    msg = await e.edit("🔄 Bot yeniden başlatılıyor...")
    
    # Restart bilgisini kaydet
    save_restart_info(e.chat_id, msg.id)
    
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def check_restart_message():
    """Restart sonrası başarı mesajı gönder"""
    chat_id, msg_id = get_restart_info()
    if chat_id and msg_id:
        try:
            uptime = get_readable_time(time.time() - start_time)
            text = f"✅ **Bot başarıyla yeniden başlatıldı!**\n\n"
            text += f"**🔢 Sürüm:** `v{__version__}`\n"
            text += f"**⏱️ Uptime:** `{uptime}`\n"
            text += f"**🔌 Modüller:** `{len(loaded_modules)}`"
            
            await client.edit_message(chat_id, msg_id, text)
            log("✅ Restart başarı mesajı gönderildi")
        except Exception as e:
            log(f"⚠️ Restart mesajı güncellenemedi: {e}")

async def main():
    log("=" * 50)
    log(f"🤖 KingTG UserBot v{__version__}")
    log(f"👨‍💻 Geliştirici: {__author__}")
    log(f"💻 Repo: {__repo__}")
    log("=" * 50)
    
    # Uyumluluk katmanını kur
    log("🔧 Uyumluluk katmanı kuruluyor...")
    setup_compatibility()
    
    log("🔄 Userbot başlatılıyor...")
    await client.start()
    me = await client.get_me()
    log(f"✅ Userbot bağlandı: {me.first_name} (@{me.username})")
    
    # Uyumluluk modülüne client'ı ver
    try:
        from userbot import events as compat_events
        compat_events.set_client(client)
        log("✅ Uyumluluk katmanı aktif")
    except Exception as e:
        log(f"⚠️ Uyumluluk katmanı yüklenemedi: {e}")
    
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
    
    # Restart sonrası mesaj kontrolü
    await check_restart_message()
    
    log("=" * 50)
    log(f"✅ Bot Hazır! Sürüm: v{__version__}")
    log(f"🔌 Yüklü Modüller: {len(loaded_modules)}")
    log(f"📱 Komutlar için .help yazın")
    log("=" * 50)
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
