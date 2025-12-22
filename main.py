import os
import sys
import asyncio
import importlib
import git
import glob
import inspect
from telethon import TelegramClient, events, Button
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = TelegramClient('userbot_session', API_ID, API_HASH)
bot = TelegramClient('bot_session', API_ID, API_HASH)

def log(text):
    print(f"\033[94m[SİSTEM]\033[0m {text}")

async def load_plugins(plugin_name):
    try:
        path = f"modules/{plugin_name}.py"
        if not os.path.exists(path): return False
        
        spec = importlib.util.spec_from_file_location(plugin_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        count = 0
        for name in dir(mod):
            obj = getattr(mod, name)
            # Sadece fonksiyonları ve Telethon eventlerini kabul et
            if inspect.isfunction(obj) and hasattr(obj, 'events'):
                client.add_event_handler(obj)
                count += 1
        return count > 0
    except Exception as e:
        log(f"❌ {plugin_name} yüklenemedi: {e}")
        return False

# --- INLINE BOT ---
@bot.on(events.InlineQuery)
async def inline_handler(event):
    if event.text == "help_menu":
        builder = event.builder
        await event.answer([builder.article(
            "Userbot Menü", 
            text="**🤖 Komut Paneli**",
            buttons=[[Button.inline("📜 Komutlar", "cmds")], [Button.inline("❌ Kapat", "close")]]
        )])

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    if data == "cmds":
        await event.edit("`.alive`, `.start`, `.pinstall`, `.update`", buttons=[[Button.inline("🔙 Geri", "back")]])
    elif data == "back":
        await event.edit("**🤖 Komut Paneli**", buttons=[[Button.inline("📜 Komutlar", "cmds")], [Button.inline("❌ Kapat", "close")]])
    elif data == "close":
        await event.delete()

# --- USERBOT ---
@client.on(events.NewMessage(outgoing=True, pattern=r'\.start'))
async def start(e): await e.edit("🚀 **Userbot Online!**")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.help'))
async def help(e):
    me = await bot.get_me()
    res = await client.inline_query(me.username, "help_menu")
    await res[0].click(e.chat_id)
    await e.delete()

@client.on(events.NewMessage(outgoing=True, pattern=r'\.pinstall'))
async def pinstall(e):
    reply = await e.get_reply_message()
    if reply and reply.file and reply.file.name.endswith('.py'):
        if not os.path.exists("modules"): os.makedirs("modules")
        path = await reply.download_media(file="modules/")
        name = os.path.basename(path).replace('.py', '')
        if await load_plugins(name):
            await e.edit(f"✅ `{name}` aktif!")
        else:
            await e.edit("❌ Modül yüklendi ama komut bulunamadı.")
    else:
        await e.edit("⚠️ Bir `.py` dosyasına yanıt verin.")

async def main():
    await client.start()
    await bot.start(bot_token=BOT_TOKEN)
    if not os.path.exists("modules"): os.makedirs("modules")
    for f in glob.glob("modules/*.py"):
        await load_plugins(os.path.basename(f).replace('.py', ''))
    log("Bot Hazır!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
