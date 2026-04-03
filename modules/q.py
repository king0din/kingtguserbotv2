# KingTG UserBot - Quote Plugin (Fixed Version)
"""
Herhangi bir sohbete kullanarak hızlıca mesajlarınızı sticker'a dönüştürüp ölümsüzleştirin.

🔧 Komutlar: .q, .qs, .qd, .q noreply, .qpaket, .qrenkler, .q random
🚨 Tür: #eğlence #çok_amaçlı


Komutlar hakkında:
.q:
Bir mesajı yanıtlayarak gönderildiğinde o mesajı sticker'a dönüştürür.

.q 3 [veya yanıtladığınız mesajdan itibaren kaçtane mesajı çıkartmaya çevirmek istiyorsanız] belirterek girerseniz o mesajları sticker'a dönüştürür

.qs:
Oluşturduğunuz sticker'i sticker paketi oluşturarak o pakete kaydeder. Doğrudan mesaj yanıtlayarak kullanırsanız önce sticker oluşturur sonra kaydeder.

.qd:
Oluşturup kaydettiğiniz stickeri yanıtlayarak kullanırsanız kaydettiğiniz stickeri paketinizden siler.

.q noreply:
Yanıtlanmış mesajda alıntı olmadan (yanıtlanan mesaj olmadan) sadece yazılan mesajı sticker yapar.

Not:
İstediğiniz çıkartmayı istediğiniz renge dönüştürebilirsiniz.
.q komutuyla yanına istediğiniz rengi yazmanız yeterlidir.

Örnek:
Mesajı yanıtlayarak!
.q kırmızı

Veya özel bir rengi
Şu şekildede hex değeri girerek kullanabilirsiniz
Örnek:
.q #ff00ff00
rastgele bir renk ile oluşturmak istiyorsanız!
.q random komutunu kullanabilirsiniz.

.qpaket:
Çıkartma paketinizi görüntüleyin.

 .qrenkler:
Kullanabileceğiniz renkleri gösterir. 
"""

from telethon import events
from telethon.tl.types import (
    User, Channel, Chat, InputStickerSetShortName,
    MessageEntityBold, MessageEntityItalic, MessageEntityCode,
    MessageEntityStrike, MessageEntityUnderline, MessageEntityTextUrl,
    MessageEntityUrl, MessageEntityMention, MessageEntityHashtag,
    MessageEntityBotCommand, MessageEntityEmail, MessageEntityPhone,
    MessageEntityPre, MessageEntitySpoiler, MessageEntityCustomEmoji,
    UserProfilePhoto, UserProfilePhotoEmpty, MessageMediaPhoto,
    MessageMediaDocument
)
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
import asyncio
import aiohttp
import base64
import os
import tempfile
import random as rnd
import re
from PIL import Image
from io import BytesIO
import json
from datetime import datetime

QUOTLY_API = "https://bot.lyo.su/quote/generate"
PACK_OWNER = "TG: @KingUser_bot"

# Log dosyası
LOG_FILE = "/tmp/quote_debug.log"

def log_debug(msg):
    """Debug mesajlarını hem console hem dosyaya yaz"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass

COLORS = {
    "siyah": "#1b1429", "black": "#1b1429",
    "beyaz": "#ffffff", "white": "#ffffff",
    "mavi": "#1e3a5f", "blue": "#1e3a5f",
    "kırmızı": "#5c1e1e", "kirmizi": "#5c1e1e", "red": "#5c1e1e",
    "yeşil": "#1e4d2b", "yesil": "#1e4d2b", "green": "#1e4d2b",
    "mor": "#2d1b4e", "purple": "#2d1b4e",
    "turuncu": "#4a2f1b", "orange": "#4a2f1b",
    "pembe": "#4a1b3d", "pink": "#4a1b3d",
    "gri": "#2a2a2a", "gray": "#2a2a2a", "grey": "#2a2a2a",
}

# Plugin yüklendiğinde
print("=" * 60)
print("🔥 QUOTE PLUGIN LOADED - DEBUG VERSION v2.0")
print(f"📝 Log dosyası: {LOG_FILE}")
print("=" * 60)

# Log dosyasını temizle
try:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== QUOTE PLUGIN DEBUG LOG ===\n\n")
except:
    pass


def strip_markdown_v2(text):
    if not text:
        return text
    
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'__', '', text)
    text = re.sub(r'~~', '', text)
    text = re.sub(r'\|\|', '', text)
    text = re.sub(r'`', '', text)
    text = re.sub(r'\\([_*\[\]()~`>#+\-=|{}.!])', r'\1', text)
    
    return text


def adjust_entities_for_cleaned_text(text, entities):
    if not text or not entities:
        return text, []
    
    cleaned_text = strip_markdown_v2(text)
    return cleaned_text, entities


def entity_to_dict(entity):
    etype = None
    extra = {}
    
    if isinstance(entity, MessageEntityBold):
        etype = "bold"
    elif isinstance(entity, MessageEntityItalic):
        etype = "italic"
    elif isinstance(entity, MessageEntityCode):
        etype = "code"
    elif isinstance(entity, MessageEntityPre):
        etype = "pre"
    elif isinstance(entity, MessageEntityStrike):
        etype = "strikethrough"
    elif isinstance(entity, MessageEntityUnderline):
        etype = "underline"
    elif isinstance(entity, MessageEntitySpoiler):
        etype = "spoiler"
    elif isinstance(entity, MessageEntityTextUrl):
        etype = "text_link"
        extra["url"] = entity.url
    elif isinstance(entity, MessageEntityUrl):
        etype = "url"
    elif isinstance(entity, MessageEntityMention):
        etype = "mention"
    elif isinstance(entity, MessageEntityHashtag):
        etype = "hashtag"
    elif isinstance(entity, MessageEntityBotCommand):
        etype = "bot_command"
    elif isinstance(entity, MessageEntityEmail):
        etype = "email"
    elif isinstance(entity, MessageEntityPhone):
        etype = "phone_number"
    elif isinstance(entity, MessageEntityCustomEmoji):
        etype = "custom_emoji"
        extra["custom_emoji_id"] = str(entity.document_id)
    
    if etype:
        return {
            "type": etype,
            "offset": entity.offset,
            "length": entity.length,
            **extra
        }
    return None


async def get_avatar_url(client, user):
    """
    Profil fotoğrafını indir - VIDEO ve NORMAL profil fotoğrafları için
    """
    try:
        if isinstance(user, User):
            # Kullanıcının profil fotoğrafı var mı kontrol et
            if isinstance(user.photo, UserProfilePhotoEmpty):
                return None
            
            # Yöntem 1: download_profile_photo ile direkt indirme
            try:
                photo_bytes = await client.download_profile_photo(user, bytes)
                
                if photo_bytes:
                    b64 = base64.b64encode(photo_bytes).decode()
                    return f"data:image/jpeg;base64,{b64}"
            except:
                pass
            
            # Yöntem 2: GetUserPhotosRequest
            try:
                photos_result = await client(GetUserPhotosRequest(
                    user_id=user.id,
                    offset=0,
                    max_id=0,
                    limit=1
                ))
                
                if photos_result and photos_result.photos:
                    photo = photos_result.photos[0]
                    
                    # Video profil fotoğrafı kontrolü
                    has_video = hasattr(photo, 'video_sizes') and photo.video_sizes
                    
                    if has_video:
                        # Stripped thumb ile dene
                        if hasattr(photo, 'stripped_thumb') and photo.stripped_thumb:
                            try:
                                thumb_data = photo.stripped_thumb
                                if isinstance(thumb_data, bytes):
                                    b64 = base64.b64encode(thumb_data).decode()
                                    return f"data:image/jpeg;base64,{b64}"
                            except:
                                pass
                        
                        # Video frame indir
                        try:
                            photo_bytes = await client.download_media(photo, bytes, thumb=-1)
                            if photo_bytes:
                                b64 = base64.b64encode(photo_bytes).decode()
                                return f"data:image/jpeg;base64,{b64}"
                        except:
                            pass
                        
                        # Video'yu direkt indir
                        try:
                            photo_bytes = await client.download_media(photo, bytes)
                            if photo_bytes:
                                b64 = base64.b64encode(photo_bytes).decode()
                                return f"data:image/jpeg;base64,{b64}"
                        except:
                            pass
                    
                    # Normal fotoğraf
                    try:
                        photo_bytes = await client.download_media(photo, bytes)
                        if photo_bytes:
                            b64 = base64.b64encode(photo_bytes).decode()
                            return f"data:image/jpeg;base64,{b64}"
                    except:
                        pass
            except:
                pass
            
            # Yöntem 3: get_profile_photos
            try:
                photos = await client.get_profile_photos(user.id, limit=1)
                if photos:
                    photo_bytes = await client.download_media(photos[0], bytes)
                    if photo_bytes:
                        b64 = base64.b64encode(photo_bytes).decode()
                        return f"data:image/jpeg;base64,{b64}"
            except:
                pass
            
        elif isinstance(user, (Channel, Chat)):
            photo_bytes = await client.download_profile_photo(user, bytes)
            if photo_bytes:
                b64 = base64.b64encode(photo_bytes).decode()
                return f"data:image/jpeg;base64,{b64}"
                
    except:
        pass
    
    return None


async def get_emoji_status_url(client, emoji_status_id):
    """
    Premium emoji status'u base64 formatında döndür
    """
    try:
        from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest
        
        # Custom emoji bilgisini al
        documents = await client(GetCustomEmojiDocumentsRequest(document_id=[int(emoji_status_id)]))
        
        if documents:
            # Emoji'yi indir
            emoji_bytes = await client.download_media(documents[0], bytes)
            
            if emoji_bytes:
                # Base64'e çevir
                b64 = base64.b64encode(emoji_bytes).decode()
                
                # WebP veya TGS formatı - API'ye uygun format belirle
                # Quotly API genelde data URI bekler
                return f"data:image/webp;base64,{b64}"
    except Exception as e:
        # Sessizce başarısız ol - emoji status opsiyonel
        pass
    
    return None


async def get_user_info(client, user):
    """Kullanıcının tam bilgilerini al (premium durumu ve emoji status dahil)"""
    user_data = {
        "id": user.id,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or ""
    }
    
    # İsim oluştur
    name = user.first_name or ""
    if user.last_name:
        name += " " + user.last_name
    
    # Premium durumu ve emoji status
    emoji_status_id = None
    try:
        full_user = await client(GetFullUserRequest(user.id))
        
        # Premium kontrolü
        if hasattr(full_user.full_user, 'premium') and full_user.full_user.premium:
            user_data["is_premium"] = True
        
        # Emoji status - premium kullanıcıların profil yanındaki emoji
        if hasattr(full_user.full_user, 'emoji_status') and full_user.full_user.emoji_status:
            emoji_status = full_user.full_user.emoji_status
            if hasattr(emoji_status, 'document_id'):
                emoji_status_id = str(emoji_status.document_id)
    except:
        pass
    
    user_data["name"] = name.strip() or "User"
    
    # Profil fotoğrafı
    avatar_url = await get_avatar_url(client, user)
    if avatar_url:
        user_data["photo"] = {"url": avatar_url}
    
    # Emoji status ekle (varsa)
    if emoji_status_id:
        emoji_url = await get_emoji_status_url(client, emoji_status_id)
        if emoji_url:
            # Quotly API'de emoji status için özel alan
            # Not: API dokümantasyonuna göre "emoji_status" veya "custom_emoji" alanı kullanılabilir
            user_data["emoji_status"] = {
                "custom_emoji_id": emoji_status_id,
                "url": emoji_url
            }
    
    return user_data


async def get_media_url(client, msg):
    """
    Mesajdaki medyayı (fotoğraf, sticker, video) base64 formatında döndür
    """
    try:
        # Fotoğraf
        if isinstance(msg.media, MessageMediaPhoto):
            log_debug(f"📷 Fotoğraf indiriliyor...")
            photo_bytes = await client.download_media(msg.media.photo, bytes)
            if photo_bytes:
                # PNG'ye çevir (daha iyi uyumluluk için)
                img = Image.open(BytesIO(photo_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = BytesIO()
                img.save(output, format='JPEG', quality=85)
                jpeg_bytes = output.getvalue()
                
                b64 = base64.b64encode(jpeg_bytes).decode()
                log_debug(f"✅ Fotoğraf base64 uzunluğu: {len(b64)} karakter")
                return f"data:image/jpeg;base64,{b64}"
        
        # Sticker, GIF, Video vb.
        elif isinstance(msg.media, MessageMediaDocument):
            doc = msg.media.document
            mime_type = doc.mime_type
            
            log_debug(f"📄 Medya tipi: {mime_type}")
            
            # Sticker (WebP veya TGS)
            if 'image/webp' in mime_type:
                log_debug("🎨 WebP sticker indiriliyor...")
                media_bytes = await client.download_media(doc, bytes)
                if media_bytes:
                    # WebP'yi JPEG'e çevir
                    try:
                        img = Image.open(BytesIO(media_bytes))
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGBA')
                        
                        # Beyaz arka plan ekle (şeffaflık varsa)
                        if img.mode == 'RGBA':
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[3])
                            img = background
                        
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85)
                        jpeg_bytes = output.getvalue()
                        
                        b64 = base64.b64encode(jpeg_bytes).decode()
                        log_debug(f"✅ Sticker base64 uzunluğu: {len(b64)} karakter")
                        return f"data:image/jpeg;base64,{b64}"
                    except Exception as e:
                        log_debug(f"❌ Sticker dönüştürme hatası: {e}")
                        # Başarısız olursa direkt base64
                        b64 = base64.b64encode(media_bytes).decode()
                        return f"data:image/webp;base64,{b64}"
            
            # TGS animasyonlu sticker - thumbnail kullan
            elif 'application/x-tgsticker' in mime_type:
                log_debug("🎨 TGS sticker (animasyonlu), thumbnail alınıyor...")
                # TGS için thumbnail al
                try:
                    thumb_bytes = await client.download_media(msg, bytes, thumb=-1)
                    if thumb_bytes:
                        b64 = base64.b64encode(thumb_bytes).decode()
                        log_debug(f"✅ TGS thumbnail base64 uzunluğu: {len(b64)} karakter")
                        return f"data:image/jpeg;base64,{b64}"
                except Exception as e:
                    log_debug(f"❌ TGS thumbnail hatası: {e}")
            
            # Video veya GIF - thumbnail al
            elif 'video' in mime_type or 'image/gif' in mime_type:
                log_debug("🎬 Video/GIF, thumbnail alınıyor...")
                try:
                    thumb_bytes = await client.download_media(msg, bytes, thumb=-1)
                    if thumb_bytes:
                        b64 = base64.b64encode(thumb_bytes).decode()
                        log_debug(f"✅ Video thumbnail base64 uzunluğu: {len(b64)} karakter")
                        return f"data:image/jpeg;base64,{b64}"
                except Exception as e:
                    log_debug(f"❌ Video thumbnail hatası: {e}")
            
            # Genel resim formatları
            elif 'image' in mime_type:
                log_debug(f"🖼️ Genel resim ({mime_type}) indiriliyor...")
                media_bytes = await client.download_media(doc, bytes)
                if media_bytes:
                    try:
                        img = Image.open(BytesIO(media_bytes))
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        output = BytesIO()
                        img.save(output, format='JPEG', quality=85)
                        jpeg_bytes = output.getvalue()
                        
                        b64 = base64.b64encode(jpeg_bytes).decode()
                        log_debug(f"✅ Resim base64 uzunluğu: {len(b64)} karakter")
                        return f"data:image/jpeg;base64,{b64}"
                    except Exception as e:
                        log_debug(f"❌ Resim dönüştürme hatası: {e}")
                        b64 = base64.b64encode(media_bytes).decode()
                        return f"data:{mime_type};base64,{b64}"
    
    except Exception as e:
        log_debug(f"❌ Medya indirme hatası: {e}")
        import traceback
        traceback.print_exc()
    
    log_debug("⚠️ Medya indirilemedi!")
    return None


async def build_message_data(client, msg, include_reply_info=True):
    """Mesajı API formatına çevir - MEDYA DESTEĞİ İLE"""
    log_debug(f"\n{'='*50}")
    log_debug(f"📨 build_message_data çağrıldı - msg.id: {msg.id}")
    
    sender = await msg.get_sender()
    
    # Gönderen bilgileri
    from_data = {"id": 0, "name": "Unknown"}
    
    if isinstance(sender, User):
        from_data = await get_user_info(client, sender)
    elif isinstance(sender, (Channel, Chat)):
        from_data = {
            "id": sender.id,
            "name": sender.title or "Group",
            "title": sender.title or "Group",
            "username": getattr(sender, 'username', "") or ""
        }
        
        avatar_url = await get_avatar_url(client, sender)
        if avatar_url:
            from_data["photo"] = {"url": avatar_url}
    
    # Mesaj metni - medya mesajları için caption kullan
    message_text = msg.text or msg.message or ""
    
    # Medya kontrolü
    has_media = hasattr(msg, 'media') and msg.media
    
    log_debug(f"📝 Text: '{message_text[:50]}...' (len={len(message_text)})")
    log_debug(f"📎 has_media: {bool(has_media)}")
    
    if has_media:
        log_debug(f"📦 Media type: {type(msg.media).__name__}")
    
    # Mesaj metnini temizle ve entity'leri ayarla
    text, entities = adjust_entities_for_cleaned_text(message_text, msg.entities or [])
    
    # Mesaj verisi
    message_data = {
        "from": from_data,
        "text": text,
        "avatar": True,
        "entities": [],
        "replyMessage": {}
    }
    
    # MEDYA EKLE (fotoğraf, sticker, video vb.)
    if has_media:
        log_debug(f"🔄 get_media_url çağrılıyor...")
        media_url = await get_media_url(client, msg)
        
        if media_url:
            # Medya tipini belirle
            media_type = "text"  # Default
            
            if isinstance(msg.media, MessageMediaPhoto):
                media_type = "text"  # Photo için text kullanılıyor
            elif isinstance(msg.media, MessageMediaDocument):
                doc = msg.media.document
                mime_type = doc.mime_type if hasattr(doc, 'mime_type') else ""
                
                # WebP sticker veya video/webm (animasyonlu sticker)
                if 'image/webp' in mime_type or 'video/webm' in mime_type:
                    media_type = "sticker"
                # TGS animasyonlu sticker
                elif 'application/x-tgsticker' in mime_type:
                    media_type = "sticker"
                # Normal video/GIF
                elif 'video' in mime_type or 'image/gif' in mime_type:
                    media_type = "text"
                else:
                    media_type = "text"
            
            log_debug(f"✅ Media URL alındı (ilk 100 char): {media_url[:100]}...")
            log_debug(f"📌 mediaType: {media_type}")
            
            # Quotly API formatı: media bir ARRAY olmalı
            message_data["media"] = [
                {
                    "url": media_url
                }
            ]
            message_data["mediaType"] = media_type
        else:
            log_debug(f"❌ Media URL alınamadı!")
    else:
        log_debug(f"ℹ️ Medya yok, atlanıyor")
    
    log_debug(f"{'='*50}\n")
    
    # Entity'leri ekle
    if entities:
        for ent in entities:
            ent_dict = entity_to_dict(ent)
            if ent_dict:
                message_data["entities"].append(ent_dict)
    
    # Reply mesajı
    if include_reply_info and msg.reply_to_msg_id:
        try:
            reply_msg = await msg.get_reply_message()
            if reply_msg:
                reply_sender = await reply_msg.get_sender()
                reply_from_data = None
                
                if isinstance(reply_sender, User):
                    reply_from_data = await get_user_info(client, reply_sender)
                elif isinstance(reply_sender, (Channel, Chat)):
                    reply_name = reply_sender.title or "Group"
                    reply_from_data = {
                        "id": reply_sender.id,
                        "name": reply_name
                    }
                    avatar_url = await get_avatar_url(client, reply_sender)
                    if avatar_url:
                        reply_from_data["photo"] = {"url": avatar_url}
                
                # Reply mesajının metnini temizle
                reply_text = reply_msg.text or reply_msg.message or ""
                
                # Reply mesajında medya kontrolü
                reply_has_media = hasattr(reply_msg, 'media') and reply_msg.media
                
                reply_text, reply_entities_list = adjust_entities_for_cleaned_text(
                    reply_text, 
                    reply_msg.entities or []
                )
                
                # Reply entity'leri
                reply_entities = []
                if reply_entities_list:
                    for ent in reply_entities_list:
                        ent_dict = entity_to_dict(ent)
                        if ent_dict:
                            reply_entities.append(ent_dict)
                
                message_data["replyMessage"] = {
                    "name": reply_from_data["name"] if reply_from_data else "Unknown",
                    "text": reply_text,
                    "entities": reply_entities,
                    "chatId": msg.chat_id
                }
                
                # Reply mesajında medya varsa ekle
                if reply_has_media:
                    reply_media_url = await get_media_url(client, reply_msg)
                    if reply_media_url:
                        # Reply için mediaType belirle
                        reply_media_type = "text"
                        
                        if isinstance(reply_msg.media, MessageMediaPhoto):
                            reply_media_type = "text"
                        elif isinstance(reply_msg.media, MessageMediaDocument):
                            doc = reply_msg.media.document
                            mime_type = doc.mime_type if hasattr(doc, 'mime_type') else ""
                            
                            if 'image/webp' in mime_type or 'application/x-tgsticker' in mime_type:
                                reply_media_type = "sticker"
                            else:
                                reply_media_type = "text"
                        
                        message_data["replyMessage"]["media"] = [
                            {
                                "url": reply_media_url
                            }
                        ]
                        message_data["replyMessage"]["mediaType"] = reply_media_type
                
                if reply_from_data:
                    message_data["replyMessage"]["from"] = reply_from_data
        except:
            import traceback
            traceback.print_exc()
    
    return message_data


async def generate_quote(messages_data, bg_color="#1b1429", fmt="webp"):
    """Quotly API'den quote oluştur"""
    payload = {
        "type": "quote",
        "format": fmt,
        "backgroundColor": bg_color,
        "width": 512,
        "height": 768,
        "scale": 2,
        "emojiBrand": "apple",
        "messages": messages_data
    }
    
    # DEBUG: Gönderilen veriyi göster
    log_debug("=" * 50)
    log_debug("QUOTLY API'YE GÖNDERİLEN VERİ:")
    import json
    log_debug(json.dumps(payload, indent=2, ensure_ascii=False)[:2000])  # İlk 2000 karakter
    log_debug("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(QUOTLY_API, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                log_debug(f"API Response Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    log_debug(f"API Response Keys: {data.keys()}")
                    log_debug(f"API Response 'ok': {data.get('ok')}")
                    
                    if data.get("result"):
                        log_debug(f"Result Keys: {data['result'].keys()}")
                        log_debug(f"Result has 'image': {'image' in data['result']}")
                        if 'image' in data['result']:
                            img_len = len(data['result']['image']) if data['result']['image'] else 0
                            log_debug(f"Image length: {img_len}")
                    
                    if data.get("ok") and data.get("result"):
                        image_b64 = data["result"].get("image")
                        if image_b64:
                            log_debug("✅ Image bulundu, decode ediliyor...")
                            return base64.b64decode(image_b64)
                        else:
                            log_debug("❌ Result'ta 'image' yok!")
                    elif data.get("image"):
                        log_debug("✅ Direkt 'image' bulundu, decode ediliyor...")
                        return base64.b64decode(data["image"])
                    elif data.get("result", {}).get("image"):
                        log_debug("✅ result.image bulundu, decode ediliyor...")
                        return base64.b64decode(data["result"]["image"])
                    else:
                        log_debug("❌ Hiçbir yerde 'image' bulunamadı!")
                        log_debug(f"Full response: {json.dumps(data, indent=2)[:1000]}")
                else:
                    error_text = await resp.text()
                    log_debug(f"API Error: {error_text[:500]}")
    except Exception as e:
        log_debug(f"Quotly hatası: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def resize_sticker(image_data, make_transparent=True):
    try:
        img = Image.open(BytesIO(image_data))
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        if make_transparent:
            pixels = img.load()
            bg_color = pixels[0, 0][:3] if len(pixels[0, 0]) >= 3 else None
            
            if bg_color:
                new_img = Image.new('RGBA', img.size)
                new_pixels = new_img.load()
                tolerance = 35
                
                for y in range(img.height):
                    for x in range(img.width):
                        pixel = pixels[x, y]
                        
                        if len(pixel) >= 3:
                            diff = sum(abs(pixel[i] - bg_color[i]) for i in range(3))
                            
                            if diff < tolerance:
                                new_pixels[x, y] = (0, 0, 0, 0)
                            else:
                                new_pixels[x, y] = pixel
                        else:
                            new_pixels[x, y] = pixel
                
                img = new_img
        
        width, height = img.size
        
        if width > height:
            new_width = 512
            new_height = int((height / width) * 512)
        else:
            new_height = 512
            new_width = int((width / height) * 512)
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue()
        
    except Exception as e:
        log_debug(f"Resize hatası: {e}")
        import traceback
        traceback.print_exc()
        return image_data


async def pack_exists(client, name):
    try:
        await client(GetStickerSetRequest(stickerset=InputStickerSetShortName(short_name=name), hash=0))
        return True
    except:
        return False


async def send_sticker_from_pack(client, chat_id, pack_name, path, reply_to):
    try:
        sticker_set = await client(GetStickerSetRequest(
            stickerset=InputStickerSetShortName(short_name=pack_name),
            hash=0
        ))
        
        if sticker_set.documents:
            last_sticker = sticker_set.documents[-1]
            await client.send_file(chat_id, last_sticker, reply_to=reply_to)
            return True
    except Exception as e:
        log_debug(f"Sticker paketten gönderilemedi: {e}")
    
    try:
        from telethon.tl.types import DocumentAttributeFilename
        await client.send_file(
            chat_id, 
            path, 
            reply_to=reply_to,
            force_document=True,
            attributes=[DocumentAttributeFilename(file_name='sticker.png')]
        )
        return True
    except Exception as e:
        log_debug(f"PNG gönderilirken hata: {e}")
        return False


async def delete_sticker_from_pack(client, pack_name, sticker):
    bot = "@Stickers"
    
    try:
        async with client.conversation(bot, timeout=60, exclusive=True) as conv:
            await conv.send_message("/cancel")
            try:
                await conv.get_response(timeout=2)
            except:
                pass
            
            await asyncio.sleep(1)
            
            await conv.send_message("/delsticker")
            resp1 = await conv.get_response()
            
            await conv.send_file(sticker)
            resp2 = await conv.get_response(timeout=10)
            
            if "deleted" in resp2.text.lower() or "removed" in resp2.text.lower():
                return True, "Sticker silindi"
            else:
                return False, resp2.text[:100]
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


from telethon.tl.types import DocumentAttributeFilename

async def create_sticker_pack(client, pack_name, title, sticker_path, emoji="💬"):
    bot = "@Stickers"
    
    if not os.path.exists(sticker_path):
        return False, "Dosya bulunamadı"
    
    try:
        async with client.conversation(bot, timeout=120, exclusive=True) as conv:
            await conv.send_message("/cancel")
            try:
                await conv.get_response(timeout=2)
            except:
                pass
            
            await asyncio.sleep(1)
            
            pack_var = await pack_exists(client, pack_name)
            
            if pack_var:
                await conv.send_message("/addsticker")
                resp1 = await conv.get_response()
                
                await conv.send_message(pack_name)
                resp2 = await conv.get_response()
                
                await conv.send_file(
                    sticker_path,
                    force_document=True,
                    attributes=[DocumentAttributeFilename(file_name='sticker.png')]
                )
                resp3 = await conv.get_response(timeout=10)
                
                if "send me an emoji" not in resp3.text.lower():
                    error_msg = resp3.text[:100] if len(resp3.text) < 100 else resp3.text[:97] + "..."
                    return False, error_msg
                
                await conv.send_message(emoji)
                resp4 = await conv.get_response()
                
                if "there we go" in resp4.text.lower():
                    await conv.send_message("/done")
                    try:
                        await conv.get_response(timeout=2)
                    except:
                        pass
                    
                    return True, "Pakete eklendi"
                
                await conv.send_message("/done")
                done_resp = await conv.get_response()
                
                if "well done" in done_resp.text.lower() or "there we go" in done_resp.text.lower():
                    try:
                        await conv.get_response(timeout=0.5)
                    except:
                        pass
                    
                    return True, "Pakete eklendi"
                else:
                    return False, done_resp.text[:100]
                
            else:
                await conv.send_message("/newpack")
                await conv.get_response()
                
                await conv.send_message(title)
                resp = await conv.get_response()
                
                await conv.send_file(
                    sticker_path,
                    force_document=True,
                    attributes=[DocumentAttributeFilename(file_name='sticker.png')]
                )
                resp = await conv.get_response(timeout=20)
                
                if "send me an emoji" not in resp.text.lower():
                    error_msg = resp.text[:100] if len(resp.text) < 100 else resp.text[:97] + "..."
                    return False, error_msg
                
                await conv.send_message(emoji)
                resp = await conv.get_response()
                
                await conv.send_message("/publish")
                resp = await conv.get_response()
                
                await conv.send_message("/skip")
                resp = await conv.get_response()
                
                await conv.send_message(pack_name)
                final_resp = await conv.get_response()
                
                if "kaboom" in final_resp.text.lower() or "t.me/addstickers" in final_resp.text.lower():
                    return True, "Paket oluşturuldu"
                else:
                    return False, final_resp.text[:100]
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


def parse_args(args):
    bg_color = "#1b1429"
    count = 1
    save = False
    include_reply = True
    
    if args:
        for p in args.split():
            pl = p.lower()
            
            if pl == "s":
                save = True
            elif pl in ["noreply", "nr"]:
                include_reply = False
            elif pl in ["random", "rastgele"]:
                bg_color = "#{:06x}".format(rnd.randint(0x1a1a1a, 0x4a4a4a))
            elif pl in COLORS:
                bg_color = COLORS[pl]
            elif pl.startswith("#") and len(pl) in [4, 7]:
                bg_color = pl
            elif pl.isdigit():
                count = min(int(pl), 10)
    
    return bg_color, count, save, include_reply


def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.q(?:\s+(.*))?$'))
    async def quote_cmd(event):
        args = (event.pattern_match.group(1) or "").strip()
        
        if args.lower() in ['d', 'delete']:
            return
        
        bg_color, count, save, include_reply = parse_args(args)
        
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit(
                "❌ **Mesaj yanıtla!**\n\n"
                "`.q` - Çıkartma\n"
                "`.q 3` - 3 mesaj\n"
                "`.q noreply` - Reply olmadan\n"
                "`.qs` - Kaydet\n"
                "`.q #ff5733` - Özel renk\n"
                "`.q mavi` - Mavi\n"
                "`.q random` - Rastgele\n"
                "`.qd` - Sticker sil"
            )
        
        await event.edit("🎨")
        
        try:
            messages_data = []
            
            # İlk mesajı ekle (yanıtlanan mesaj)
            main_msg_data = await build_message_data(client, reply, include_reply_info=include_reply)
            messages_data.append(main_msg_data)
            
            # Eğer count > 1 ise, sonraki mesajları da topla
            if count > 1:
                collected = 0
                async for msg in client.iter_messages(event.chat_id, min_id=reply.id, limit=50, reverse=True):
                    # İlk mesajı atlama ve BOŞ MESAJLARI ATLAMA
                    if msg.id == reply.id:
                        continue
                    
                    # MEDYA veya METİN varsa dahil et
                    # Boş mesajları atla (ne text ne media olan)
                    has_text = bool(msg.text or msg.message)
                    has_media = bool(hasattr(msg, 'media') and msg.media)
                    
                    if not has_text and not has_media:
                        continue
                    
                    msg_data = await build_message_data(client, msg, include_reply_info=include_reply)
                    messages_data.append(msg_data)
                    collected += 1
                    
                    if collected >= count - 1:
                        break
            
            fmt = "png" if save else "webp"
            image_data = await generate_quote(messages_data, bg_color, fmt)
            
            if not image_data:
                return await event.edit("❌ **API hatası!**")
            
            if save:
                image_data = resize_sticker(image_data, make_transparent=True)
            
            with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as f:
                f.write(image_data)
                path = f.name
            
            if save:
                await event.edit("📦 **Kaydediliyor...**")
                
                me = await client.get_me()
                pack = f"q_{me.id}_by_KingUser_bot"
                title = f"Quotes | {PACK_OWNER}"
                
                ok, msg = await create_sticker_pack(client, pack, title, path, "💬")
                
                if ok:
                    await send_sticker_from_pack(client, event.chat_id, pack, path, reply.id)
                else:
                    await client.send_file(
                        event.chat_id, 
                        path, 
                        reply_to=reply.id,
                        force_document=True,
                        attributes=[DocumentAttributeFilename(file_name='sticker.png')]
                    )
                
                os.unlink(path)
                
                link = f"https://t.me/addstickers/{pack}"
                if ok:
                    await event.edit(f"✅ **{msg}!**\n📦 [Paket]({link})")
                else:
                    await event.edit(f"❌ {msg}")
            else:
                await client.send_file(event.chat_id, path, reply_to=reply.id)
                await event.delete()
                os.unlink(path)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            await event.edit(f"❌ `{e}`")
    
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.qs(?:\s+(.*))?$'))
    async def quote_save_cmd(event):
        args = (event.pattern_match.group(1) or "").strip()
        bg_color, count, _, include_reply = parse_args(args)
        
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("❌ Mesaj yanıtla!")
        
        await event.edit("🎨")
        
        try:
            if reply.sticker:
                await event.edit("📥 **Sticker indiriliyor...**")
                
                sticker_bytes = await reply.download_media(bytes)
                
                if not sticker_bytes:
                    return await event.edit("❌ Sticker indirilemedi!")
                
                image_data = resize_sticker(sticker_bytes, make_transparent=False)
                
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    f.write(image_data)
                    path = f.name
                
                await event.edit("📦 **Pakete ekleniyor...**")
                
                me = await client.get_me()
                pack = f"q_{me.id}_by_KingUser_bot"
                title = f"Quotes | {PACK_OWNER}"
                
                ok, msg = await create_sticker_pack(client, pack, title, path, "💬")
                
                if ok:
                    await send_sticker_from_pack(client, event.chat_id, pack, path, reply.id)
                else:
                    await client.send_file(
                        event.chat_id, 
                        path, 
                        reply_to=reply.id,
                        force_document=True,
                        attributes=[DocumentAttributeFilename(file_name='sticker.png')]
                    )
                
                os.unlink(path)
                
                link = f"https://t.me/addstickers/{pack}"
                if ok:
                    await event.edit(f"✅ **{msg}!**\n📦 [Paket]({link})")
                else:
                    await event.edit(f"❌ {msg}")
                
            else:
                messages_data = []
                
                # İlk mesajı ekle
                main_msg_data = await build_message_data(client, reply, include_reply_info=include_reply)
                messages_data.append(main_msg_data)
                
                # Sonraki mesajları topla
                if count > 1:
                    collected = 0
                    async for msg in client.iter_messages(event.chat_id, min_id=reply.id, limit=50, reverse=True):
                        if msg.id == reply.id:
                            continue
                        
                        # MEDYA veya METİN varsa dahil et
                        has_text = bool(msg.text or msg.message)
                        has_media = bool(hasattr(msg, 'media') and msg.media)
                        
                        if not has_text and not has_media:
                            continue
                        
                        msg_data = await build_message_data(client, msg, include_reply_info=include_reply)
                        messages_data.append(msg_data)
                        collected += 1
                        if collected >= count - 1:
                            break
                
                image_data = await generate_quote(messages_data, bg_color, "png")
                
                if not image_data:
                    return await event.edit("❌ **API hatası!**")
                
                image_data = resize_sticker(image_data, make_transparent=True)
                
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    f.write(image_data)
                    path = f.name
                
                await event.edit("📦 **Kaydediliyor...**")
                
                me = await client.get_me()
                pack = f"q_{me.id}_by_KingUser_bot"
                title = f"Quotes | {PACK_OWNER}"
                
                ok, msg = await create_sticker_pack(client, pack, title, path, "💬")
                
                if ok:
                    await send_sticker_from_pack(client, event.chat_id, pack, path, reply.id)
                else:
                    await client.send_file(
                        event.chat_id, 
                        path, 
                        reply_to=reply.id,
                        force_document=True,
                        attributes=[DocumentAttributeFilename(file_name='sticker.png')]
                    )
                
                os.unlink(path)
                
                link = f"https://t.me/addstickers/{pack}"
                if ok:
                    await event.edit(f"✅ **{msg}!**\n📦 [Paket]({link})")
                else:
                    await event.edit(f"❌ {msg}")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await event.edit(f"❌ Hata: `{type(e).__name__}: {str(e)[:50]}`")
    
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.qd$'))
    async def delete_sticker_cmd(event):
        reply = await event.get_reply_message()
        if not reply:
            return await event.edit("❌ Silinecek sticker'a yanıtla!")
        
        if not reply.sticker:
            return await event.edit("❌ Bu bir sticker değil!")
        
        await event.edit("🗑️ **Siliniyor...**")
        
        try:
            me = await client.get_me()
            pack = f"q_{me.id}_by_KingUser_bot"
            
            if not await pack_exists(client, pack):
                return await event.edit("❌ Sticker paketi bulunamadı!")
            
            ok, msg = await delete_sticker_from_pack(client, pack, reply.sticker)
            
            if ok:
                await event.edit(f"✅ **{msg}!**")
            else:
                await event.edit(f"❌ {msg}")
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await event.edit(f"❌ Hata: `{type(e).__name__}: {str(e)[:50]}`")
    
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.qpaket$'))
    async def pack_info(event):
        me = await client.get_me()
        pack = f"q_{me.id}_by_KingUser_bot"
        link = f"https://t.me/addstickers/{pack}"
        
        if await pack_exists(client, pack):
            await event.edit(f"📦 [Paket]({link})")
        else:
            await event.edit("📦 Yok. `.qs` ile oluştur")
    
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.qlog$'))
    async def show_log(event):
        """Debug log dosyasını göster"""
        try:
            if os.path.exists(LOG_FILE):
                await event.edit("📋 Log dosyası gönderiliyor...")
                await client.send_file(event.chat_id, LOG_FILE, caption="🐛 Quote Plugin Debug Log")
                await event.delete()
            else:
                await event.edit("❌ Log dosyası bulunamadı!")
        except Exception as e:
            await event.edit(f"❌ Hata: {e}")
    
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.qrenkler$'))
    async def colors_cmd(event):
        await event.edit(
            "🎨 **Renkler:**\n\n"
            "`siyah` `beyaz` `mavi` `kırmızı` `yeşil` `mor` `turuncu` `pembe` `gri`\n"
            "`random` - Rastgele\n"
            "`#HEX` - Özel (örn: `#ff5733`)\n"
            "`noreply` - Reply olmadan\n\n"
            "**Komutlar:**\n"
            "`.q` - Quote oluştur\n"
            "`.qs` - Quote kaydet\n"
            "`.qd` - Sticker sil\n"
            "`.qpaket` - Paket linki\n"
            "`.qlog` - Debug log dosyası"
        )