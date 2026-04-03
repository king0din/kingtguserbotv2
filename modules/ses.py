# KingTG UserBot - Ses (TTS) Plugin
# Metni doğal sese dönüştürür
# requires: edge-tts
#
# Kullanım:
#   .ses <metin>
#   .ses (mesaja yanıt vererek)
#   .ses (txt dosyasına yanıt vererek)
#   .sesler (mevcut sesleri listele)
#   .sesayar <ses_kodu> (varsayılan sesi değiştir)
"""
Herhangi bir sohbete yazdığınız yazıyı yada bir yazıyı yanıtlayarak kullandığınızda o yazıyı ses dosyası olarak gönderir.

🔧 Komutlar:  .ses, .sesler, .sesayar
🚨 Tür: #eğlence


Komular hakında:
.ses: Bu komutla yanıtlanan veya girilen metni sese çevir.
      Ayrıca bir .txt dosyasına yanıt vererek dosyadaki metni sese çevirebilirsiniz.

.sesler: Bu komut gönderildiği zaman mevcut seslerin listesini ve değiştirme komutlarının listesini gösterir.

.sesayar: Bu komutla ses ayarı yapılır.
Örnek: .sesayar kadın
Örnek2: .sesayar erkek

Veya başka bir dile çevirmek istiyorsanız başına ülke kodu ekleyerek:
Örnek: .sesayar en-erkek
Örnek2: .sesayar en-kadın
İngilizce dilindeki yazıyı ingilizce sese çevirir.

Not: Türkçe için ülke kodu girmenize gerek yok sadece cinsiyet yazmanız yeterlidir.
Örnek: .sesayar erkek
"""

from telethon import events
import asyncio
import os
import tempfile
import edge_tts

# Varsayılan ses (Türkçe erkek)
DEFAULT_VOICE = "tr-TR-AhmetNeural"

# Mevcut ses ayarı
current_voice = DEFAULT_VOICE

# Popüler Türkçe sesler
TURKISH_VOICES = {
    "erkek": "tr-TR-AhmetNeural",
    "kadın": "tr-TR-EmelNeural",
}

# Diğer dil sesleri
OTHER_VOICES = {
    "en-erkek": "en-US-ChristopherNeural",
    "en-kadın": "en-US-JennyNeural",
    "de-erkek": "de-DE-ConradNeural",
    "de-kadın": "de-DE-KatjaNeural",
    "fr-erkek": "fr-FR-HenriNeural",
    "fr-kadın": "fr-FR-DeniseNeural",
    "ar-erkek": "ar-SA-HamedNeural",
    "ar-kadın": "ar-SA-ZariyahNeural",
    "ru-erkek": "ru-RU-DmitryNeural",
    "ru-kadın": "ru-RU-SvetlanaNeural",
}

ALL_VOICES = {**TURKISH_VOICES, **OTHER_VOICES}


async def get_text_from_file(client, message):
    """Dosyadan metin oku"""
    try:
        # Dosyayı indir
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        
        await client.download_media(message, tmp_path)
        
        # Dosyayı oku
        with open(tmp_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Geçici dosyayı sil
        os.unlink(tmp_path)
        
        return text.strip()
    except UnicodeDecodeError:
        # UTF-8 ile okunamazsa latin-1 dene
        try:
            with open(tmp_path, 'r', encoding='latin-1') as f:
                text = f.read()
            os.unlink(tmp_path)
            return text.strip()
        except:
            pass
    except Exception:
        pass
    
    try:
        os.unlink(tmp_path)
    except:
        pass
    
    return None


def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ses(?:\s+(.+))?$'))
    async def tts_cmd(event):
        global current_voice
        
        text = event.pattern_match.group(1)
        
        # Yanıt verilen mesajdan metin al
        reply = await event.get_reply_message()
        if reply and not text:
            # Önce dosya var mı kontrol et
            if reply.document:
                # Dosya adını kontrol et
                file_name = ""
                if hasattr(reply.document, 'attributes'):
                    for attr in reply.document.attributes:
                        if hasattr(attr, 'file_name'):
                            file_name = attr.file_name or ""
                            break
                
                # .txt dosyası mı?
                if file_name.lower().endswith('.txt') or reply.document.mime_type == 'text/plain':
                    await event.edit("📄 **Dosya okunuyor...**")
                    text = await get_text_from_file(client, reply)
                    
                    if not text:
                        await event.edit("❌ Dosya okunamadı!")
                        return
                else:
                    await event.edit("❌ Sadece `.txt` dosyaları desteklenir!")
                    return
            else:
                # Normal metin mesajı
                text = reply.raw_text
        
        if not text:
            await event.edit(
                "❌ **Kullanım:**\n"
                "`.ses <metin>`\n"
                "veya bir mesaja yanıt vererek: `.ses`\n"
                "veya bir `.txt` dosyasına yanıt vererek: `.ses`"
            )
            return
        
        if len(text) > 10000:
            await event.edit("❌ Metin çok uzun! (Max 10000 karakter)")
            return
        
        char_count = len(text)
        await event.edit(f"🎙️ **Ses oluşturuluyor...**\n`{char_count} karakter`")
        
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Edge TTS ile sese dönüştür
            communicate = edge_tts.Communicate(text, current_voice)
            await communicate.save(tmp_path)
            
            # Ses dosyasını gönder
            await event.edit("📤 **Gönderiliyor...**")
            
            if reply:
                await client.send_file(
                    event.chat_id,
                    tmp_path,
                    voice_note=True,
                    reply_to=reply.id
                )
            else:
                await client.send_file(
                    event.chat_id,
                    tmp_path,
                    voice_note=True
                )
            
            # Komutu sil
            await event.delete()
            
            # Geçici dosyayı sil
            os.unlink(tmp_path)
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.sesler$'))
    async def list_voices(event):
        text = "🎙️ **Mevcut Sesler**\n\n"
        
        text += "**🇹🇷 Türkçe:**\n"
        for name, code in TURKISH_VOICES.items():
            marker = " ✓" if code == current_voice else ""
            text += f"• `{name}` - {code}{marker}\n"
        
        text += "\n**🌍 Diğer Diller:**\n"
        for name, code in OTHER_VOICES.items():
            marker = " ✓" if code == current_voice else ""
            text += f"• `{name}` - {code}{marker}\n"
        
        text += f"\n**Şu anki ses:** `{current_voice}`"
        text += "\n\n💡 Değiştirmek için: `.sesayar <isim>`"
        
        await event.edit(text)
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.sesayar\s+(\S+)$'))
    async def set_voice(event):
        global current_voice
        
        voice_input = event.pattern_match.group(1).lower()
        
        if voice_input in ALL_VOICES:
            current_voice = ALL_VOICES[voice_input]
            await event.edit(f"✅ Ses değiştirildi: `{current_voice}`")
        elif voice_input.count("-") >= 2:
            # Direkt ses kodu girilmiş olabilir (örn: tr-TR-AhmetNeural)
            current_voice = voice_input
            await event.edit(f"✅ Ses değiştirildi: `{current_voice}`")
        else:
            await event.edit(f"❌ Ses bulunamadı: `{voice_input}`\n\n💡 Mevcut sesler için: `.sesler`")
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.tts(?:\s+(.+))?$'))
    async def tts_alias(event):
        """Alias for .ses command"""
        global current_voice
        
        text = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if reply and not text:
            # Önce dosya var mı kontrol et
            if reply.document:
                file_name = ""
                if hasattr(reply.document, 'attributes'):
                    for attr in reply.document.attributes:
                        if hasattr(attr, 'file_name'):
                            file_name = attr.file_name or ""
                            break
                
                if file_name.lower().endswith('.txt') or reply.document.mime_type == 'text/plain':
                    await event.edit("📄 **Dosya okunuyor...**")
                    text = await get_text_from_file(client, reply)
                    
                    if not text:
                        await event.edit("❌ Dosya okunamadı!")
                        return
                else:
                    await event.edit("❌ Sadece `.txt` dosyaları desteklenir!")
                    return
            else:
                text = reply.raw_text
        
        if not text:
            await event.edit(
                "❌ **Kullanım:**\n"
                "`.tts <metin>`\n"
                "veya bir mesaja yanıt vererek: `.tts`\n"
                "veya bir `.txt` dosyasına yanıt vererek: `.tts`"
            )
            return
        
        if len(text) > 10000:
            await event.edit("❌ Metin çok uzun! (Max 10000 karakter)")
            return
        
        char_count = len(text)
        await event.edit(f"🎙️ **Ses oluşturuluyor...**\n`{char_count} karakter`")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            
            communicate = edge_tts.Communicate(text, current_voice)
            await communicate.save(tmp_path)
            
            await event.edit("📤 **Gönderiliyor...**")
            
            if reply:
                await client.send_file(
                    event.chat_id,
                    tmp_path,
                    voice_note=True,
                    reply_to=reply.id
                )
            else:
                await client.send_file(
                    event.chat_id,
                    tmp_path,
                    voice_note=True
                )
            
            await event.delete()
            os.unlink(tmp_path)
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")
            try:
                os.unlink(tmp_path)
            except:
                pass