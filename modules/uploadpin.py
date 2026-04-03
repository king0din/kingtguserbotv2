# KingTG UserBot - Plugin Yükleyici
# .uploadpin komutu ile plugin dosyalarını sohbete gönderir

from telethon import events
import os

def register(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.uploadpin\s+(.+)$'))
    async def upload_plugin(event):
        plugin_name = event.pattern_match.group(1).strip()
        
        # .py uzantısı yoksa ekle
        if not plugin_name.endswith('.py'):
            plugin_name += '.py'
        
        # Plugin dizinleri
        plugin_dirs = ['plugins', 'modules', '.']
        
        plugin_path = None
        for dir in plugin_dirs:
            path = os.path.join(dir, plugin_name)
            if os.path.exists(path):
                plugin_path = path
                break
        
        if not plugin_path:
            return await event.edit(f"❌ **Plugin bulunamadı:** `{plugin_name}`\n\n"
                                   f"📁 Aranan dizinler: `plugins/`, `modules/`, `./`")
        
        try:
            await event.edit(f"📤 **Yükleniyor:** `{plugin_name}`")
            
            # Dosyayı gönder
            await event.client.send_file(
                event.chat_id,
                plugin_path,
                caption=f"📦 **Plugin:** `{plugin_name}`",
                force_document=True
            )
            
            await event.delete()
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.uploadpin$'))
    async def upload_plugin_help(event):
        await event.edit("❌ **Kullanım:** `.uploadpin <plugin_adı>`\n\n"
                        "**Örnek:**\n"
                        "`.uploadpin muzik`\n"
                        "`.uploadpin whisper.py`")