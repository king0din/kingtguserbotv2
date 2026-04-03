# KingTG UserBot - Multi Session Plugin v5
# Her hesap kendi pluginlerini yönetir
# Her plugin izole instance olarak yüklenir

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
import json
import asyncio
import glob
import types

SESSIONS_FILE = "sessions.json"
active_sessions = {}

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)

def get_plugin_dir(user_id):
    """Kullanıcının plugin klasörü"""
    d = f"plugins_{user_id}"
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def load_plugin_isolated(client, filepath, user_id):
    """Plugin'i izole instance olarak yükle"""
    filename = os.path.basename(filepath)
    module_name = f"session_{user_id}_{filename[:-3]}"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Yeni izole modül oluştur
        module = types.ModuleType(module_name)
        module.__file__ = filepath
        module.__dict__['__builtins__'] = __builtins__
        
        # Temel importları ekle
        exec("""
import os, sys, asyncio, json, time, re, hashlib, glob
from telethon import events, Button, TelegramClient
from telethon.sessions import StringSession
""", module.__dict__)
        
        # Kodu çalıştır (bu modülün kendi global'leri olacak)
        exec(compile(code, filepath, 'exec'), module.__dict__)
        
        if hasattr(module, 'register'):
            module.register(client)
            return module, True
        
        return module, False
        
    except Exception as e:
        print(f"[SESSION-{user_id}] ❌ {filename}: {e}")
        return None, False

def load_user_plugins(client, user_id):
    """Kullanıcının tüm pluginlerini yükle"""
    plugin_dir = get_plugin_dir(user_id)
    loaded = 0
    modules = {}
    
    for filepath in glob.glob(os.path.join(plugin_dir, '*.py')):
        filename = os.path.basename(filepath)
        if filename.startswith('__'):
            continue
        
        module, success = load_plugin_isolated(client, filepath, user_id)
        if success:
            modules[filename] = module
            loaded += 1
            print(f"[SESSION-{user_id}] ✅ {filename}")
    
    return loaded, modules

def register(client):
    api_id = client.api_id
    api_hash = client.api_hash
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.session\s+(.+)$'))
    async def add_session(event):
        session_string = event.pattern_match.group(1).strip()
        
        if len(session_string) < 100:
            return await event.edit("❌ **Geçersiz session string!**")
        
        await event.edit("🔄 **Session başlatılıyor...**")
        
        try:
            new_client = TelegramClient(StringSession(session_string), api_id, api_hash)
            await new_client.start()
            
            me = await new_client.get_me()
            user_id = me.id
            
            sessions = load_sessions()
            if str(user_id) in sessions:
                await new_client.disconnect()
                return await event.edit(f"⚠️ **Bu hesap zaten ekli!**\n\n"
                                       f"👤 {me.first_name}\n"
                                       f"🆔 `{user_id}`")
            
            # Plugin klasörünü oluştur
            plugin_dir = get_plugin_dir(user_id)
            
            # Session komutlarını ekle
            setup_session_commands(new_client, user_id, api_id, api_hash)
            
            # Mevcut pluginleri yükle (varsa)
            loaded, modules = load_user_plugins(new_client, user_id)
            
            # Kaydet
            sessions[str(user_id)] = {
                "session": session_string,
                "user_id": user_id,
                "first_name": me.first_name,
                "username": me.username
            }
            save_sessions(sessions)
            
            active_sessions[user_id] = {
                "client": new_client,
                "info": sessions[str(user_id)],
                "modules": modules
            }
            
            await event.edit(f"✅ **Session eklendi!**\n\n"
                           f"👤 **İsim:** {me.first_name}\n"
                           f"🆔 **ID:** `{user_id}`\n"
                           f"📁 **Klasör:** `{plugin_dir}/`\n"
                           f"📦 **Plugin:** {loaded}\n\n"
                           f"**O hesapta kullan:**\n"
                           f"• `.spinstall` - Plugin yükle\n"
                           f"• `.splugins` - Plugin listesi")
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.sessionlist$'))
    async def list_sessions(event):
        sessions = load_sessions()
        
        if not sessions:
            return await event.edit("📭 **Hiç session eklenmemiş!**")
        
        txt = "📋 **Ekli Hesaplar**\n\n"
        
        for uid, info in sessions.items():
            status = "🟢" if int(uid) in active_sessions else "🔴"
            plugin_dir = get_plugin_dir(uid)
            plugin_count = len(glob.glob(os.path.join(plugin_dir, '*.py')))
            
            txt += f"{status} **{info.get('first_name', '?')}**\n"
            txt += f"   🆔 `{uid}`\n"
            txt += f"   📦 {plugin_count} plugin\n\n"
        
        txt += f"━━━━━━━━━━━━━━━\n"
        txt += f"**Toplam:** {len(sessions)} hesap"
        
        await event.edit(txt)

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.sessiondel\s+(\d+)$'))
    async def del_session(event):
        user_id = event.pattern_match.group(1).strip()
        sessions = load_sessions()
        
        if user_id not in sessions:
            return await event.edit(f"❌ **Session bulunamadı:** `{user_id}`")
        
        info = sessions[user_id]
        
        if int(user_id) in active_sessions:
            try:
                await active_sessions[int(user_id)]["client"].disconnect()
                del active_sessions[int(user_id)]
            except:
                pass
        
        del sessions[user_id]
        save_sessions(sessions)
        
        await event.edit(f"✅ **Session silindi!**\n\n"
                        f"👤 {info.get('first_name', '?')}\n"
                        f"🆔 `{user_id}`\n\n"
                        f"📁 Plugin klasörü: `plugins_{user_id}/`\n"
                        f"(Manuel silmek istersen)")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.sessionrestart$'))
    async def restart_sessions(event):
        sessions = load_sessions()
        
        if not sessions:
            return await event.edit("📭 **Hiç session yok!**")
        
        await event.edit("🔄 **Yeniden başlatılıyor...**")
        
        for uid in list(active_sessions.keys()):
            try:
                await active_sessions[uid]["client"].disconnect()
            except:
                pass
        active_sessions.clear()
        
        started = 0
        for uid, info in sessions.items():
            try:
                new_client = TelegramClient(StringSession(info["session"]), api_id, api_hash)
                await new_client.start()
                
                setup_session_commands(new_client, int(uid), api_id, api_hash)
                loaded, modules = load_user_plugins(new_client, int(uid))
                
                active_sessions[int(uid)] = {
                    "client": new_client,
                    "info": info,
                    "modules": modules
                }
                started += 1
            except Exception as e:
                print(f"[SESSION] ❌ {uid}: {e}")
        
        await event.edit(f"✅ **{started}/{len(sessions)} session başlatıldı!**")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.session$'))
    async def session_help(event):
        await event.edit("📱 **Multi-Session**\n\n"
                        "**Ana Hesap:**\n"
                        "• `.session <string>` - Ekle\n"
                        "• `.sessionlist` - Liste\n"
                        "• `.sessiondel <id>` - Sil\n"
                        "• `.sessionrestart` - Yeniden başlat\n\n"
                        "**Eklenen Hesapta:**\n"
                        "• `.spinstall` - Plugin yükle\n"
                        "• `.sdelpin <ad>` - Plugin sil\n"
                        "• `.splugins` - Liste\n"
                        "• `.sreload` - Yeniden yükle")

    # Otomatik başlat
    async def auto_start():
        await asyncio.sleep(5)
        sessions = load_sessions()
        
        for uid, info in sessions.items():
            if int(uid) in active_sessions:
                continue
            try:
                new_client = TelegramClient(StringSession(info["session"]), api_id, api_hash)
                await new_client.start()
                
                setup_session_commands(new_client, int(uid), api_id, api_hash)
                loaded, modules = load_user_plugins(new_client, int(uid))
                
                active_sessions[int(uid)] = {
                    "client": new_client,
                    "info": info,
                    "modules": modules
                }
                print(f"[SESSION] ✅ {info.get('first_name', uid)} - {loaded} plugin")
            except Exception as e:
                print(f"[SESSION] ❌ {uid}: {e}")
    
    asyncio.get_event_loop().create_task(auto_start())


def setup_session_commands(new_client, user_id, api_id, api_hash):
    """Eklenen hesap için komutlar"""
    plugin_dir = get_plugin_dir(user_id)
    
    @new_client.on(events.NewMessage(outgoing=True, pattern=r'^\.spinstall$'))
    async def spinstall(event):
        reply = await event.get_reply_message()
        
        if not reply or not reply.document:
            return await event.edit("❌ **Bir .py dosyasına yanıt ver!**")
        
        try:
            filename = reply.document.attributes[0].file_name
        except:
            return await event.edit("❌ **Dosya adı alınamadı!**")
        
        if not filename.endswith('.py'):
            return await event.edit("❌ **Sadece .py dosyaları!**")
        
        filepath = os.path.join(plugin_dir, filename)
        
        await event.edit(f"📥 **İndiriliyor:** `{filename}`")
        
        try:
            await new_client.download_media(reply, filepath)
            
            # İzole olarak yükle
            module, success = load_plugin_isolated(new_client, filepath, user_id)
            
            if success:
                if user_id in active_sessions:
                    active_sessions[user_id]["modules"][filename] = module
                await event.edit(f"✅ **Plugin yüklendi:** `{filename}`\n\n"
                               f"Artık komutları kullanabilirsin!")
            else:
                await event.edit(f"⚠️ **Kaydedildi ama register() yok:** `{filename}`")
                
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @new_client.on(events.NewMessage(outgoing=True, pattern=r'^\.sdelpin\s+(.+)$'))
    async def sdelpin(event):
        name = event.pattern_match.group(1).strip()
        if not name.endswith('.py'):
            name += '.py'
        
        filepath = os.path.join(plugin_dir, name)
        
        if not os.path.exists(filepath):
            return await event.edit(f"❌ **Bulunamadı:** `{name}`")
        
        os.remove(filepath)
        
        if user_id in active_sessions and name in active_sessions[user_id].get("modules", {}):
            del active_sessions[user_id]["modules"][name]
        
        await event.edit(f"✅ **Silindi:** `{name}`")

    @new_client.on(events.NewMessage(outgoing=True, pattern=r'^\.splugins$'))
    async def splugins(event):
        plugins = glob.glob(os.path.join(plugin_dir, '*.py'))
        
        if not plugins:
            return await event.edit(f"📭 **Plugin yok!**\n\n"
                                   f"`.spinstall` ile yükle\n"
                                   f"📁 `{plugin_dir}/`")
        
        txt = f"📦 **Pluginler** ({user_id})\n\n"
        for p in plugins:
            name = os.path.basename(p)
            loaded = "✅" if name in active_sessions.get(user_id, {}).get("modules", {}) else "⚠️"
            txt += f"{loaded} `{name}`\n"
        
        txt += f"\n**Toplam:** {len(plugins)}"
        await event.edit(txt)

    @new_client.on(events.NewMessage(outgoing=True, pattern=r'^\.sreload$'))
    async def sreload(event):
        await event.edit("🔄 **Pluginler yeniden yükleniyor...**")
        
        loaded, modules = load_user_plugins(new_client, user_id)
        
        if user_id in active_sessions:
            active_sessions[user_id]["modules"] = modules
        
        await event.edit(f"✅ **{loaded} plugin yüklendi!**")

    @new_client.on(events.NewMessage(outgoing=True, pattern=r'^\.sping$'))
    async def sping(event):
        import time
        start = time.time()
        m = await event.edit("🏓")
        end = time.time()
        await m.edit(f"🏓 `{(end-start)*1000:.0f}ms`")