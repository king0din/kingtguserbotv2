# KingTG UserBot - Plugin Yardım (Otomatik)
# .phelp komutu ile tüm pluginlerin komutlarını otomatik tespit eder

from telethon import events
import os
import re
import glob

def get_plugin_commands():
    """Tüm plugin dosyalarından komutları otomatik tespit et"""
    plugins = {}
    
    # Plugin dizinleri - olası tüm yerler
    plugin_dirs = [
        'plugins',
        'modules', 
        'Plugins',
        'Modules',
        '.',  # Ana dizin
        'userbot/plugins',
        'userbot/modules',
    ]
    
    # Pattern'lar - komutları bulmak için
    patterns = [
        r"pattern\s*=\s*r?['\"][\^]?\\?\.(\w+)",  # pattern=r'^\.komut veya pattern='\.komut
    ]
    
    found_files = set()  # Aynı dosyayı tekrar taramayı önle
    
    for dir in plugin_dirs:
        if not os.path.exists(dir):
            continue
            
        for filepath in glob.glob(os.path.join(dir, '*.py')):
            filename = os.path.basename(filepath)
            
            # Zaten tarandıysa atla
            if filename in found_files:
                continue
            found_files.add(filename)
            
            plugin_name = filename.replace('.py', '')
            
            # __init__, __pycache__ ve main atla
            if plugin_name.startswith('__') or plugin_name == 'main':
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Komutları bul
                commands = set()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    commands.update(matches)
                
                # Açıklama bul (dosyanın başındaki yorum)
                desc_match = re.search(r'^#\s*(.+?)(?:\n|$)', content)
                description = desc_match.group(1).strip() if desc_match else plugin_name.capitalize()
                
                if commands:
                    plugins[plugin_name] = {
                        'açıklama': description,
                        'komutlar': sorted(commands),
                        'dosya': filename
                    }
                    
            except Exception as e:
                print(f"[PHELP] {filename} okunamadı: {e}")
    
    return plugins

def register(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.phelp(?:\s+(.+))?$'))
    async def plugin_help(event):
        query = event.pattern_match.group(1)
        
        # Pluginleri tara
        plugins = get_plugin_commands()
        
        if not plugins:
            return await event.edit("❌ **Hiç plugin bulunamadı!**\n\n"
                                   "📁 `plugins/` veya `modules/` klasörüne plugin ekleyin.")
        
        if query:
            # Belirli bir plugin için yardım
            query = query.strip().lower().replace('.py', '')
            
            if query in plugins:
                plugin = plugins[query]
                txt = f"**📦 {plugin['açıklama']}**\n"
                txt += f"📄 Dosya: `{plugin['dosya']}`\n\n"
                txt += "**Komutlar:**\n"
                for cmd in plugin['komutlar']:
                    txt += f"• `.{cmd}`\n"
                return await event.edit(txt)
            else:
                return await event.edit(f"❌ **Plugin bulunamadı:** `{query}`\n\n"
                                       f"📋 Mevcut: `{', '.join(plugins.keys())}`")
        
        # Tüm pluginlerin özeti
        txt = "**📚 Yüklü Pluginler**\n\n"
        
        total_cmds = 0
        for name, plugin in sorted(plugins.items()):
            cmd_count = len(plugin['komutlar'])
            total_cmds += cmd_count
            
            # İlk 3 komutu göster
            preview = ', '.join([f".{c}" for c in plugin['komutlar'][:3]])
            if cmd_count > 3:
                preview += f" +{cmd_count - 3}"
            
            txt += f"**{name}** (`{cmd_count}` komut)\n"
            txt += f"   `{preview}`\n\n"
        
        txt += "━━━━━━━━━━━━━━━\n"
        txt += f"📊 **{len(plugins)}** plugin, **{total_cmds}** komut\n"
        txt += f"💡 `.phelp <plugin>` detay için"
        
        await event.edit(txt)

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.komutlar$'))
    async def all_commands(event):
        """Tüm komutları tek listede göster"""
        plugins = get_plugin_commands()
        
        if not plugins:
            return await event.edit("❌ Hiç plugin bulunamadı!")
        
        txt = "**📜 Tüm Komutlar**\n\n"
        
        for name, plugin in sorted(plugins.items()):
            txt += f"**{name}:**\n"
            txt += " • " + " • ".join([f"`.{c}`" for c in plugin['komutlar']]) + "\n\n"
        
        # Mesaj çok uzunsa kısalt
        if len(txt) > 4000:
            txt = txt[:3900] + "\n\n... _(liste çok uzun)_"
        
        await event.edit(txt)