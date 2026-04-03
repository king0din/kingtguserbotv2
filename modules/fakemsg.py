"""
Sahte Telegram mesajı görseli oluşturur (PNG).

🔧 Komutlar: .fakemsg, .fakehelp
🚨 Tür: #eğlence

Komutlar hakkında:
.fakemsg @username <mesaj> - Username ile sahte mesaj
.fakemsg <user_id> <mesaj> - ID ile sahte mesaj
[mesajı yanıtla] .fakemsg <mesaj> - Reply ile sahte mesaj

Örnekler:
.fakemsg @ahmet Merhaba ben Ahmet ve bu sahte!
.fakemsg 123456789 Ben username olmayan birisiyim
[Birinin mesajını yanıtla] .fakemsg Bu sahte mesaj

NOT: 
- Sadece hedef kişinin bilgilerini kullanır
- Sizin profilinize DOKUNMAZ
- Gerçek mesaj değil, sadece PNG görseli

UYARI: Kötü amaçla kullanmayın!
"""

import asyncio
import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from telethon import events
from userbot import bot
from userbot.events import register as r
from userbot.cmdhelp import CmdHelp

# Renkler (Telegram Dark Theme)
DARK_BG = (33, 33, 33)           # Arka plan
MSG_BG = (45, 45, 45)            # Mesaj balonu
TEXT_COLOR = (255, 255, 255)     # Beyaz metin
TIMESTAMP_COLOR = (170, 170, 170) # Gri zaman
NAME_COLOR = (94, 171, 255)      # Mavi isim
CHECKMARK_COLOR = (80, 170, 255) # Mavi tik

# Mesaj boyutları
MSG_WIDTH = 600
MSG_PADDING = 20
AVATAR_SIZE = 50
MSG_MARGIN = 15


def wrap_text(text, font, max_width):
    """Metni satırlara böl"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def create_circular_avatar(image_data, size):
    """Profil fotoğrafını daire şeklinde kırp"""
    try:
        # Resmi aç
        img = Image.open(io.BytesIO(image_data))
        
        # Kare yap (merkezi al)
        width, height = img.size
        min_size = min(width, height)
        left = (width - min_size) // 2
        top = (height - min_size) // 2
        right = left + min_size
        bottom = top + min_size
        img = img.crop((left, top, right, bottom))
        
        # Boyutlandır
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Daire maskesi oluştur
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Maskeyi uygula
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(img, (0, 0))
        output.putalpha(mask)
        
        return output
    except:
        return None


def create_default_avatar(name, size):
    """Profil fotoğrafı yoksa varsayılan avatar oluştur"""
    # Rastgele arka plan rengi (ismin ilk harfine göre)
    colors = [
        (255, 87, 87),   # Kırmızı
        (255, 167, 38),  # Turuncu
        (255, 214, 10),  # Sarı
        (76, 217, 100),  # Yeşil
        (90, 200, 250),  # Mavi
        (180, 100, 255), # Mor
        (255, 105, 180), # Pembe
    ]
    
    char = name[0].upper() if name else '?'
    color_index = ord(char) % len(colors)
    bg_color = colors[color_index]
    
    # Avatar oluştur
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Harf yaz
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 2)
    except:
        font = ImageFont.load_default()
    
    # Metni ortala
    bbox = draw.textbbox((0, 0), char, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - size // 10)
    
    draw.text(position, char, fill=(255, 255, 255), font=font)
    
    # Daire maskesi
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    
    return img


async def get_profile_photo(client, user_id):
    """Kullanıcının profil fotoğrafını indir"""
    try:
        # Profil fotoğrafını indir
        photo = await client.download_profile_photo(user_id, bytes)
        if photo:
            return photo
        return None
    except:
        return None


def create_fake_message(name, message, avatar_img=None, timestamp=None):
    """Sahte mesaj görseli oluştur"""
    try:
        # Font yükle
        try:
            font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            font_msg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        except:
            font_name = ImageFont.load_default()
            font_msg = ImageFont.load_default()
            font_time = ImageFont.load_default()
        
        # Timestamp
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        # Mesaj satırlarına böl
        max_text_width = MSG_WIDTH - AVATAR_SIZE - MSG_PADDING * 3 - 10
        lines = wrap_text(message, font_msg, max_text_width)
        
        # Mesaj yüksekliğini hesapla
        line_height = 25
        msg_height = len(lines) * line_height + MSG_PADDING * 2 + 30
        
        # Toplam yükseklik
        total_height = max(AVATAR_SIZE + MSG_PADDING * 2, msg_height + MSG_PADDING * 2 + 20)
        
        # Ana canvas oluştur
        img = Image.new('RGB', (MSG_WIDTH, total_height), DARK_BG)
        draw = ImageDraw.Draw(img)
        
        # Avatar ekle
        avatar_x = MSG_PADDING
        avatar_y = MSG_PADDING
        
        if avatar_img:
            img.paste(avatar_img, (avatar_x, avatar_y), avatar_img)
        else:
            default_avatar = create_default_avatar(name, AVATAR_SIZE)
            img.paste(default_avatar, (avatar_x, avatar_y), default_avatar)
        
        # İsim
        name_x = avatar_x + AVATAR_SIZE + MSG_MARGIN
        name_y = avatar_y
        draw.text((name_x, name_y), name, fill=NAME_COLOR, font=font_name)
        
        # Mesaj balonu
        balloon_x = name_x
        balloon_y = name_y + 25
        balloon_width = MSG_WIDTH - balloon_x - MSG_PADDING
        balloon_height = len(lines) * line_height + MSG_PADDING * 2
        
        # Yuvarlatılmış köşeli dikdörtgen (mesaj balonu)
        draw.rounded_rectangle(
            [balloon_x, balloon_y, balloon_x + balloon_width, balloon_y + balloon_height],
            radius=15,
            fill=MSG_BG
        )
        
        # Mesaj metni
        text_x = balloon_x + MSG_PADDING
        text_y = balloon_y + MSG_PADDING
        
        for line in lines:
            draw.text((text_x, text_y), line, fill=TEXT_COLOR, font=font_msg)
            text_y += line_height
        
        # Zaman damgası ve tik
        time_y = balloon_y + balloon_height + 5
        time_text = f"{timestamp}"
        
        # Zaman
        draw.text((balloon_x + balloon_width - 80, time_y), time_text, fill=TIMESTAMP_COLOR, font=font_time)
        
        # Çift tik (✓✓)
        check_x = balloon_x + balloon_width - 25
        draw.text((check_x, time_y), "✓✓", fill=CHECKMARK_COLOR, font=font_time)
        
        return img
    
    except Exception as e:
        return None


@r(outgoing=True, pattern="^.fakemsg(?: |$)(.*)")
async def fake_message(q):
    """Sahte mesaj oluştur"""
    # Sadece userbot hesabı kullanabilir
    try:
        userbot_id = (await q.client.get_me()).id
        if q.sender_id != userbot_id:
            return
    except:
        return
    
    args = q.pattern_match.group(1).strip()
    
    # Yanıtlanan mesaj var mı kontrol et
    reply_msg = await q.get_reply_message()
    
    user_id = None
    user_name = None
    message_text = None
    
    # REPLY İLE KULLANIM
    if reply_msg:
        user_id = reply_msg.sender_id
        
        # Mesaj metni - args varsa onu kullan, yoksa "Sahte mesaj"
        if args:
            message_text = args
        else:
            message_text = "Bu sahte bir mesaj!"
        
        # Kullanıcı bilgilerini al
        try:
            user_entity = await q.client.get_entity(user_id)
            user_name = user_entity.first_name or "Kullanıcı"
        except:
            user_name = "Kullanıcı"
    
    # ARGÜMANLA KULLANIM
    elif args:
        parts = args.split(None, 1)
        
        if len(parts) < 2:
            await q.edit(
                "❌ **Mesaj eksik!**\n\n"
                "**Doğru kullanım:**\n"
                "• `.fakemsg @username mesaj`\n"
                "• `.fakemsg 123456789 mesaj`\n"
                "• `[mesajı yanıtla] .fakemsg mesaj`\n\n"
                "**Örnek:**\n"
                "`.fakemsg @ahmet Merhaba ben Ahmet!`"
            )
            return
        
        target = parts[0]
        message_text = parts[1]
        
        # @ ile başlıyorsa username
        if target.startswith("@"):
            try:
                user_entity = await q.client.get_entity(target)
                user_id = user_entity.id
                user_name = user_entity.first_name or target
            except Exception as e:
                await q.edit(f"❌ **Kullanıcı bulunamadı:** `{target}`")
                return
        
        # Sayıysa ID
        elif target.isdigit():
            user_id = int(target)
            try:
                user_entity = await q.client.get_entity(user_id)
                user_name = user_entity.first_name or "Kullanıcı"
            except:
                user_name = f"Kullanıcı {user_id}"
        
        else:
            await q.edit(
                "❌ **Geçersiz format!**\n\n"
                "**Doğru kullanım:**\n"
                "• `.fakemsg @username mesaj`\n"
                "• `.fakemsg 123456789 mesaj`\n"
                "• `[mesajı yanıtla] .fakemsg mesaj`"
            )
            return
    
    else:
        await q.edit(
            "❌ **Kullanım hatası!**\n\n"
            "**Doğru kullanım:**\n"
            "• `.fakemsg @username mesaj`\n"
            "• `.fakemsg 123456789 mesaj`\n"
            "• `[mesajı yanıtla] .fakemsg mesaj`\n\n"
            "**Örnekler:**\n"
            "`.fakemsg @ahmet Merhaba ben Ahmet!`\n"
            "`.fakemsg 123456789 Bu sahte mesaj`\n\n"
            "💡 Detaylı yardım: `.fakehelp`"
        )
        return
    
    # İşlem mesajı
    await q.edit("🎨 **Sahte mesaj oluşturuluyor...**")
    
    try:
        # Profil fotoğrafını indir
        avatar_data = await get_profile_photo(q.client, user_id)
        avatar_img = None
        
        if avatar_data:
            avatar_img = create_circular_avatar(avatar_data, AVATAR_SIZE)
        
        # Sahte mesaj görseli oluştur
        timestamp = datetime.now().strftime("%H:%M")
        fake_img = create_fake_message(user_name, message_text, avatar_img, timestamp)
        
        if not fake_img:
            await q.edit("❌ **Görsel oluşturulamadı!**")
            return
        
        # PNG olarak kaydet
        output = io.BytesIO()
        fake_img.save(output, format='PNG')
        output.seek(0)
        
        # Görseli gönder
        await q.client.send_file(
            q.chat_id,
            output,
            caption=f"🎭 **Sahte Mesaj**\n\n👤 **Kullanıcı:** {user_name}\n⚠️ **Bu gerçek bir mesaj değildir!**"
        )
        
        # Komutu sil
        await q.delete()
    
    except Exception as e:
        await q.edit(f"❌ **Hata oluştu:** `{str(e)}`")


@r(outgoing=True, pattern="^.fakehelp$")
async def fake_help(q):
    """Yardım mesajı"""
    # Sadece userbot hesabı kullanabilir
    try:
        userbot_id = (await q.client.get_me()).id
        if q.sender_id != userbot_id:
            return
    except:
        return
    
    help_text = """
**🎭 SAHTE MESAJ OLUŞTURUCU - YARDIM**

**⚠️ ÖNEMLİ UYARI:**
Bu özellik sadece eğlence amaçlıdır!
Kötü niyetle kullanmayın, kandırmayın, dolandırmayın.

---

**📌 NASIL KULLANILIR?**

**1️⃣ Username ile:**
`.fakemsg @username <mesaj>`

**Örnek:**
`.fakemsg @ahmet Merhaba ben Ahmet ve bu sahte!`

**2️⃣ User ID ile:**
`.fakemsg <user_id> <mesaj>`

**Örnek:**
`.fakemsg 123456789 Ben username olmayan birisiyim`

**3️⃣ Reply ile (Kolay yöntem):**
```
[Birinin mesajını yanıtla]
.fakemsg <mesaj>
```

**Örnek:**
```
[Ahmet'in mesajını yanıtla]
.fakemsg Bu sahte bir mesaj!
```

---

**🛡️ GÜVENLİK:**

✅ **Sizin profilinize DOKUNMAZ**
- Adınızı değiştirmez
- Profil fotoğrafınızı değiştirmez
- Hiçbir bilginizi kaydetmez

✅ **Sadece görsel üretir**
- Gerçek mesaj DEĞIL
- PNG fotoğraf olarak gönderir
- Telegram'da sahte mesaj atamaz

✅ **Hedef kişinin bilgilerini kullanır**
- Adını çeker
- Profil fotoğrafını çeker
- Görsel üzerinde gösterir

---

**🎨 GÖRSEL ÖZELLİKLERİ:**

• **Dark Theme:** Telegram karanlık tema
• **Gerçekçi görünüm:** Telegram UI'ı gibi
• **Profil fotoğrafı:** Dairesel avatar
• **Zaman damgası:** Şimdiki saat
• **Çift tik:** Görüldü işareti
• **Yuvarlatılmış köşeler:** Mesaj balonu

---

**💡 KULLANIM SENARYOLARİ:**

**🎭 Eğlence:**
Arkadaşlarınızla şaka yapmak için

**📸 Screenshot:**
Sahte konuşma ekran görüntüsü

**🎬 İçerik Üretimi:**
Video/story için sahte mesaj görseli

---

**⚙️ TEKNİK BİLGİLER:**

• **Format:** PNG görsel
• **Boyut:** 600x değişken piksel
• **Profil fotoğrafı:** Otomatik indirir
• **Varsayılan avatar:** Fotograf yoksa renkli harf
• **Metin sarma:** Uzun mesajlar otomatik bölünür

---

**❓ SSS:**

**S: Gerçek mesaj atar mı?**
C: Hayır, sadece PNG görsel oluşturur.

**S: Profilim değişir mi?**
C: Hayır, sadece hedef kişinin bilgilerini kullanır.

**S: İsim kaydeden botlar görür mü?**
C: Hayır, çünkü gerçek profil değişikliği yok.

**S: Herhangi bir hesaba yapabilir miyim?**
C: Evet, username veya ID biliyorsanız.

**S: Uzun mesajlar çalışır mı?**
C: Evet, otomatik satırlara bölünür.

---

**🚨 YASAL UYARI:**

Bu araç sadece eğlence içindir.
Kimseyi kandırmak, dolandırmak veya zarar vermek için kullanmayın.
Oluşan her türlü sorumluluğu kullanıcı üstlenir.

---

**📞 DESTEK:**

Sorun yaşarsanız:
• Komutu doğru yazdığınızdan emin olun
• Kullanıcının mevcut olduğunu kontrol edin
• Bot yetkilerini kontrol edin
"""
    
    try:
        await q.edit(help_text)
    except:
        pass


# ==========================================
# CMDHELP AYARLARI
# ==========================================

Help = CmdHelp('fakemsg')
Help.add_command('fakemsg @username <mesaj>', None, 'Username ile sahte mesaj görseli oluştur')
Help.add_command('fakemsg <user_id> <mesaj>', None, 'User ID ile sahte mesaj görseli oluştur')
Help.add_command('fakemsg <mesaj> (reply)', None, 'Yanıtlanan kişi adına sahte mesaj oluştur')
Help.add_command('fakehelp', None, 'Detaylı yardım ve kullanım kılavuzu')
Help.add_info('Sahte Telegram mesajı görseli oluştur - Sadece eğlence için!')
Help.add()
