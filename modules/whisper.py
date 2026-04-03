# KingTG UserBot - Whisper (Fısıltı) Plugin
# Sadece belirtilen kişi mesajı okuyabilir
# 
# Kullanım:
#   1. Inline (log'a düşmez): @botadi whisper @kullanici mesaj
#   2. Inline (log'a düşmez): @botadi whisper 123456789 mesaj  
#   3. Komut + yanıt (log'a düşmez): Mesaja yanıt ver + .w mesaj
#   4. Komut (log'a düşmez): .w @kullanici mesaj

from telethon import events, Button
import hashlib
import time
import asyncio

# Whisper verileri
WHISPERS = {}

def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.w(?:hisper)?\s+(.+)'))
    async def whisper_cmd(event):
        full_text = event.pattern_match.group(1).strip()
        
        target_id = None
        target_name = None
        message = None
        
        reply = await event.get_reply_message()
        
        if reply:
            # Yanıt verilen mesajdan kullanıcı al
            target_id = reply.sender_id
            message = full_text
            
            try:
                target_user = await client.get_entity(target_id)
                target_name = target_user.first_name or "Kullanıcı"
                if hasattr(target_user, 'username') and target_user.username:
                    target_name = f"@{target_user.username}"
            except:
                target_name = f"Kullanıcı ({target_id})"
        else:
            # İlk kelimeyi al (kullanıcı adı veya ID olabilir)
            parts = full_text.split(maxsplit=1)
            
            if len(parts) < 2:
                await event.edit("🔐")
                await asyncio.sleep(0.5)
                await event.delete()
                return
            
            target_input = parts[0].lstrip('@')
            message = parts[1]
            
            try:
                if target_input.isdigit():
                    target_id = int(target_input)
                    try:
                        target_user = await client.get_entity(target_id)
                        target_name = target_user.first_name or "Kullanıcı"
                        if hasattr(target_user, 'username') and target_user.username:
                            target_name = f"@{target_user.username}"
                    except:
                        target_name = f"Kullanıcı ({target_id})"
                else:
                    target_user = await client.get_entity(target_input)
                    target_id = target_user.id
                    target_name = target_user.first_name or "Kullanıcı"
                    if hasattr(target_user, 'username') and target_user.username:
                        target_name = f"@{target_user.username}"
            except:
                await event.edit("🔐")
                await asyncio.sleep(0.5)
                await event.delete()
                return
        
        if not target_id or not message:
            await event.edit("🔐")
            await asyncio.sleep(0.5)
            await event.delete()
            return
        
        sender_id = event.sender_id
        whisper_id = hashlib.md5(f"{sender_id}{target_id}{time.time()}".encode()).hexdigest()[:10]
        
        # Whisper'ı kaydet
        WHISPERS[whisper_id] = {
            'sender_id': sender_id,
            'target_id': target_id,
            'message': message,
            'read': False,
            'target_name': target_name
        }
        
        try:
            import sys
            main = sys.modules.get('__main__')
            if main and hasattr(main, 'bot'):
                # Önce mesajı gizle
                await event.edit("🔐")
                
                bot_me = await main.bot.get_me()
                results = await client.inline_query(bot_me.username, f"wh_{whisper_id}")
                
                if results:
                    if reply:
                        await results[0].click(event.chat_id, reply_to=reply.id)
                    else:
                        await results[0].click(event.chat_id)
                    
                    # Komutu sil
                    try:
                        await event.delete()
                    except:
                        pass
            else:
                await event.edit("🔐")
                await asyncio.sleep(0.5)
                await event.delete()
        except:
            try:
                await event.edit("🔐")
                await asyncio.sleep(0.5)
                await event.delete()
            except:
                pass
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.w(?:hisper)?$'))
    async def whisper_help(event):
        help_text = """**🔐 Whisper Plugin**

**Komut Kullanımı:**
• `.w @kullanıcı mesaj`
• `.w kullanıcı_id mesaj`
• Yanıt vererek: `.w mesaj`

**Inline Kullanımı (önerilen):**
• `@botadi w @kullanıcı mesaj`
• `@botadi w kullanıcı_id mesaj`

**Kısa komut:** `.w` = `.whisper`"""
        await event.edit(help_text)


def register_bot(bot, client):
    
    @bot.on(events.InlineQuery(pattern=r'^wh_(.+)$'))
    async def inline_whisper(event):
        whisper_id = event.pattern_match.group(1)
        whisper = WHISPERS.get(whisper_id)
        
        if not whisper:
            await event.answer([], cache_time=0)
            return
        
        target_name = whisper.get('target_name', 'Kullanıcı')
        
        result = event.builder.article(
            title="🔐 Whisper",
            description=f"Sadece {target_name} görebilir",
            text=f"🔐 **Gizli Mesaj**\n\n👤 Sadece **{target_name}** okuyabilir.",
            buttons=[[Button.inline("👁️ Mesajı Gör", f"wr_{whisper_id}")]]
        )
        await event.answer([result], cache_time=0)
    
    @bot.on(events.InlineQuery(pattern=r'^w\s+@?(\S+)\s+(.+)$'))
    async def inline_whisper_direct(event):
        """Direkt inline whisper: @bot whisper @kullanici mesaj"""
        target_input = event.pattern_match.group(1)
        message = event.pattern_match.group(2)
        sender_id = event.sender_id
        
        target_id = None
        target_name = None
        
        try:
            if target_input.isdigit():
                target_id = int(target_input)
                try:
                    target_user = await client.get_entity(target_id)
                    target_name = target_user.first_name or "Kullanıcı"
                    if hasattr(target_user, 'username') and target_user.username:
                        target_name = f"@{target_user.username}"
                except:
                    target_name = f"Kullanıcı ({target_id})"
            else:
                target_user = await client.get_entity(target_input)
                target_id = target_user.id
                target_name = target_user.first_name or "Kullanıcı"
                if hasattr(target_user, 'username') and target_user.username:
                    target_name = f"@{target_user.username}"
        except:
            await event.answer([
                event.builder.article(
                    title="❌ Kullanıcı bulunamadı",
                    description=f"{target_input} bulunamadı",
                    text=f"❌ Kullanıcı bulunamadı: `{target_input}`"
                )
            ], cache_time=0)
            return
        
        whisper_id = hashlib.md5(f"{sender_id}{target_id}{time.time()}".encode()).hexdigest()[:10]
        
        WHISPERS[whisper_id] = {
            'sender_id': sender_id,
            'target_id': target_id,
            'message': message,
            'read': False,
            'target_name': target_name
        }
        
        msg_preview = message[:25] + "..." if len(message) > 25 else message
        
        result = event.builder.article(
            title=f"🔐 Whisper → {target_name}",
            description=msg_preview,
            text=f"🔐 **Gizli Mesaj**\n\n👤 Sadece **{target_name}** okuyabilir.",
            buttons=[[Button.inline("👁️ Mesajı Gör", f"wr_{whisper_id}")]]
        )
        await event.answer([result], cache_time=0)
    
    @bot.on(events.InlineQuery(pattern=r'^whisper\s*$'))
    async def inline_whisper_help(event):
        await event.answer([
            event.builder.article(
                title="🔐 Whisper Kullanımı",
                description="@kingodinbot whisper @kullanici veya id mesaj",
                text="**🔐 Whisper Kullanımı**\n\n`@kingodinbot whisper @kullanici veya id mesaj`\n`@kingodinbot whisper 123456789 mesaj`"
            )
        ], cache_time=0)
    
    @bot.on(events.CallbackQuery(pattern=r'^wr_(.+)$'))
    async def read_whisper(event):
        match = event.pattern_match.group(1)
        whisper_id = match.decode() if isinstance(match, bytes) else match
        whisper = WHISPERS.get(whisper_id)
        
        if not whisper:
            await event.answer("❌ Mesaj bulunamadı!", alert=True)
            return
        
        user_id = event.sender_id
        sender_id = whisper['sender_id']
        target_id = whisper['target_id']
        message = whisper['message']
        target_name = whisper.get('target_name', 'Kullanıcı')
        
        if user_id == target_id:
            whisper['read'] = True
            await event.answer(f"💬 {message}", alert=True)
            try:
                await event.edit(
                    f"🔐 **Gizli Mesaj**\n\n👤 Alıcı: **{target_name}**\n✅ Okundu",
                    buttons=[[Button.inline("✅ Okundu", "wh_done")]]
                )
            except:
                pass
        elif user_id == sender_id:
            status = "✅ Okundu" if whisper['read'] else "⏳ Okunmadı"
            await event.answer(f"📤 Mesajın:\n{message}\n\n{status}", alert=True)
        else:
            await event.answer("🚫 Bu mesaj sana ait değil!", alert=True)
    
    @bot.on(events.CallbackQuery(pattern=r'^wh_done$'))
    async def whisper_done(event):
        await event.answer("✅ Mesaj okundu!", alert=True)