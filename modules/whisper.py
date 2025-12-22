# KingTG UserBot - Whisper (Fısıltı) Plugin
# Sadece belirtilen kişi mesajı okuyabilir
# Kullanım: .whisper @kullanıcı mesaj
# veya bir mesaja yanıt vererek: .whisper mesaj

from telethon import events, Button
from telethon.tl.functions.users import GetFullUserRequest
import hashlib
import time

# Whisper verileri - {whisper_id: {sender_id, target_id, message, read}}
_whispers = {}

def register(client):
    
    # Bot referansını al (inline için gerekli)
    _bot = None
    
    async def get_bot():
        nonlocal _bot
        if _bot is None:
            # Bot client'ı bul
            import sys
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, 'bot'):
                _bot = main_module.bot
        return _bot
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.whisper(?:\s+@?(\S+))?\s+(.+)'))
    async def whisper_cmd(event):
        """Whisper komutu - .whisper @kullanıcı mesaj"""
        target_username = event.pattern_match.group(1)
        message = event.pattern_match.group(2)
        
        target_id = None
        target_name = None
        
        # Yanıt verilen mesajdan kullanıcı al
        reply = await event.get_reply_message()
        if reply and not target_username:
            target_id = reply.sender_id
            try:
                target_user = await client.get_entity(target_id)
                target_name = target_user.first_name
                if target_user.username:
                    target_name = f"@{target_user.username}"
            except:
                target_name = f"Kullanıcı"
        elif target_username:
            # Username'den kullanıcı bul
            try:
                if target_username.isdigit():
                    target_id = int(target_username)
                else:
                    target_user = await client.get_entity(target_username)
                    target_id = target_user.id
                    target_name = target_user.first_name
                    if target_user.username:
                        target_name = f"@{target_user.username}"
            except Exception as e:
                await event.edit(f"❌ Kullanıcı bulunamadı: `{target_username}`")
                return
        else:
            await event.edit("❌ **Kullanım:**\n`.whisper @kullanıcı mesaj`\nveya bir mesaja yanıt vererek:\n`.whisper mesaj`")
            return
        
        if not target_id:
            await event.edit("❌ Hedef kullanıcı belirlenemedi!")
            return
        
        # Whisper ID oluştur
        sender_id = event.sender_id
        whisper_id = hashlib.md5(f"{sender_id}{target_id}{time.time()}".encode()).hexdigest()[:12]
        
        # Whisper'ı kaydet
        _whispers[whisper_id] = {
            'sender_id': sender_id,
            'target_id': target_id,
            'message': message,
            'read': False,
            'target_name': target_name
        }
        
        # Inline bot ile mesaj gönder
        try:
            bot = await get_bot()
            if bot:
                bot_user = await bot.get_me()
                results = await client.inline_query(bot_user.username, f"whisper_{whisper_id}")
                if results:
                    await results[0].click(event.chat_id)
                    await event.delete()
                else:
                    await event.edit("❌ Inline sorgu başarısız!")
            else:
                await event.edit("❌ Bot bulunamadı!")
        except Exception as e:
            await event.edit(f"❌ Hata: {e}")
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.whisper$'))
    async def whisper_help(event):
        """Whisper yardım"""
        help_text = """**🔐 Whisper (Fısıltı) Plugin**

**Kullanım:**
• `.whisper @kullanıcı mesajınız`
• Bir mesaja yanıt vererek: `.whisper mesajınız`

**Özellikler:**
• Sadece hedef kişi mesajı görebilir
• Mesaj okunduktan sonra işaretlenir
• Diğer kullanıcılar mesajı göremez

**Örnek:**
`.whisper @ahmet Merhaba, bu gizli mesaj!`"""
        await event.edit(help_text)


def register_bot(bot, client):
    """Bot event handler'larını kaydet"""
    
    # Whisper verileri için referans
    import sys
    main_module = sys.modules.get('__main__')
    
    @bot.on(events.InlineQuery(pattern=r'^whisper_(.+)'))
    async def inline_whisper(event):
        """Inline whisper göster"""
        whisper_id = event.pattern_match.group(1)
        
        # Whisper'ı bul
        whisper = _whispers.get(whisper_id)
        
        if not whisper:
            await event.answer([
                event.builder.article(
                    "Whisper Bulunamadı",
                    text="❌ Bu whisper bulunamadı veya süresi dolmuş.",
                )
            ])
            return
        
        target_name = whisper.get('target_name', 'Kullanıcı')
        
        await event.answer([
            event.builder.article(
                "🔐 Gizli Mesaj",
                text=f"🔐 **Gizli Mesaj**\n\n👤 Alıcı: **{target_name}**\n\n💬 Mesajı okumak için aşağıdaki butona tıkla.",
                buttons=[
                    [Button.inline("👁️ Mesajı Oku", f"read_{whisper_id}")]
                ]
            )
        ])
    
    @bot.on(events.CallbackQuery(pattern=r'^read_(.+)'))
    async def read_whisper(event):
        """Whisper'ı oku"""
        whisper_id = event.pattern_match.group(1).decode()
        
        whisper = _whispers.get(whisper_id)
        
        if not whisper:
            await event.answer("❌ Bu mesaj bulunamadı veya süresi dolmuş!", alert=True)
            return
        
        user_id = event.sender_id
        sender_id = whisper['sender_id']
        target_id = whisper['target_id']
        message = whisper['message']
        target_name = whisper.get('target_name', 'Kullanıcı')
        
        # Sadece gönderen veya hedef okuyabilir
        if user_id == target_id:
            # Hedef kişi okuyor
            whisper['read'] = True
            await event.answer(f"💬 Mesaj:\n\n{message}", alert=True)
            
            # Mesajı güncelle
            try:
                await event.edit(
                    f"🔐 **Gizli Mesaj**\n\n👤 Alıcı: **{target_name}**\n\n✅ _Mesaj okundu_",
                    buttons=[[Button.inline("✅ Okundu", "already_read")]]
                )
            except:
                pass
                
        elif user_id == sender_id:
            # Gönderen kendi mesajını görüyor
            status = "✅ Okundu" if whisper['read'] else "⏳ Okunmadı"
            await event.answer(f"📤 Gönderdiğin mesaj:\n\n{message}\n\nDurum: {status}", alert=True)
        else:
            # Başka biri okumaya çalışıyor
            await event.answer("🚫 Bu mesaj sana ait değil!", alert=True)
    
    @bot.on(events.CallbackQuery(pattern=r'^already_read$'))
    async def already_read(event):
        """Zaten okundu bildirimi"""
        await event.answer("✅ Bu mesaj zaten okundu!", alert=True)
