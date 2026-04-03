# KingTG UserBot - Şarkı Sözleri Plugin
# .lyrics ve .singer komutları

from telethon import events
import os
import asyncio

# Genius API Key - https://genius.com/api-clients adresinden alabilirsin
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY") or os.getenv("GENIUS", None)

try:
    import lyricsgenius
    GENIUS_AVAILABLE = True
except ImportError:
    GENIUS_AVAILABLE = False

def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.lyrics\s+(.+)$'))
    async def lyrics_cmd(event):
        if not GENIUS_AVAILABLE:
            return await event.edit("❌ **lyricsgenius yüklü değil!**\n\n`pip install lyricsgenius`")
        
        if not GENIUS_API_KEY:
            return await event.edit("❌ **GENIUS_API_KEY ayarlanmamış!**\n\n"
                                   "1. https://genius.com/api-clients adresinden API key al\n"
                                   "2. `.env` dosyasına ekle:\n"
                                   "`GENIUS_API_KEY=your_key_here`")
        
        query = event.pattern_match.group(1)
        
        # Sanatçı - Şarkı formatı kontrolü
        if " - " not in query:
            return await event.edit("❌ **Yanlış format!**\n\n"
                                   "**Kullanım:** `.lyrics Sanatçı - Şarkı`\n"
                                   "**Örnek:** `.lyrics Tarkan - Şımarık`")
        
        try:
            parts = query.split(" - ", 1)
            artist = parts[0].strip()
            song = parts[1].strip()
        except:
            return await event.edit("❌ **Sanatçı ve şarkı adını doğru girin!**")
        
        await event.edit(f"🔍 **Aranıyor:** `{artist} - {song}`")
        
        try:
            genius = lyricsgenius.Genius(GENIUS_API_KEY, verbose=False)
            result = genius.search_song(song, artist)
            
            if not result:
                return await event.edit(f"❌ **Bulunamadı:** `{artist} - {song}`")
            
            lyrics_text = result.lyrics
            
            # Çok uzunsa dosya olarak gönder
            if len(lyrics_text) > 4000:
                await event.edit("📝 **Şarkı sözleri çok uzun, dosya olarak gönderiliyor...**")
                
                with open("/tmp/lyrics.txt", "w", encoding="utf-8") as f:
                    f.write(f"🎵 {artist} - {song}\n\n{lyrics_text}")
                
                await event.client.send_file(
                    event.chat_id,
                    "/tmp/lyrics.txt",
                    caption=f"🎵 **{artist} - {song}**",
                    reply_to=event.id
                )
                await event.delete()
                os.remove("/tmp/lyrics.txt")
            else:
                await event.edit(f"🎵 **{artist} - {song}**\n\n```{lyrics_text[:3900]}```")
                
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.singer\s+(.+)$'))
    async def singer_cmd(event):
        """Şarkı sözlerini satır satır gösterir (karaoke modu)"""
        if not GENIUS_AVAILABLE:
            return await event.edit("❌ **lyricsgenius yüklü değil!**\n\n`pip install lyricsgenius`")
        
        if not GENIUS_API_KEY:
            return await event.edit("❌ **GENIUS_API_KEY ayarlanmamış!**")
        
        query = event.pattern_match.group(1)
        
        if " - " not in query:
            return await event.edit("❌ **Kullanım:** `.singer Sanatçı - Şarkı`")
        
        try:
            parts = query.split(" - ", 1)
            artist = parts[0].strip()
            song = parts[1].strip()
        except:
            return await event.edit("❌ **Sanatçı ve şarkı adını doğru girin!**")
        
        await event.edit(f"🔍 **Aranıyor:** `{artist} - {song}`")
        
        try:
            genius = lyricsgenius.Genius(GENIUS_API_KEY, verbose=False)
            result = genius.search_song(song, artist)
            
            if not result:
                return await event.edit(f"❌ **Bulunamadı:** `{artist} - {song}`")
            
            await event.edit(f"🎤 **Söylüyor:** `{artist} - {song}`")
            await asyncio.sleep(2)
            
            # Satır satır göster
            lines = result.lyrics.splitlines()
            for line in lines[:50]:  # Max 50 satır
                if line.strip():
                    try:
                        await event.edit(f"🎤 `{line}`")
                        await asyncio.sleep(2)
                    except:
                        pass
            
            await event.edit(f"🎵 **Bitti:** `{artist} - {song}`")
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.lyrics$'))
    async def lyrics_help(event):
        await event.edit("🎵 **Şarkı Sözleri**\n\n"
                        "**Kullanım:**\n"
                        "`.lyrics Sanatçı - Şarkı`\n"
                        "`.singer Sanatçı - Şarkı` (karaoke)\n\n"
                        "**Örnek:**\n"
                        "`.lyrics Tarkan - Şımarık`\n"
                        "`.singer Sezen Aksu - Geri Dön`")