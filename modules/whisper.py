# KingTG UserBot - Whisper (Fısıltı) Plugin
# Sadece belirtilen kişi mesajı okuyabilir
# Kullanım: .whisper @kullanıcı mesaj

from telethon import events, Button
import hashlib
import time

# Whisper verileri
WHISPERS = {}

def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.whisper(?:\s+@?(\S+))?\s+(.+)'))
    async def whisper_cmd(event):
        target_input = event.pattern_match.group(1)
        message = event.pattern_match.group(2)
        
        target_id = None
        target_name = None
        
        reply = await event.get_reply_message()
        if reply and not target_input:
            target_id = reply.sender_id
            try:
                target_user = await client.get_entity(target_id)
                target_name = target_user.first_name
                if target_user.username:
                    target_name = f"@{target_user.username}"
            except:
                target_name = "Kullanıcı"
        elif target_input:
            try:
                if target_input.isdigit():
                    target_id = int(target_input)
                    target_user = await client.get_entity(target_id)
                else:
                    target_user = await client.get_entity(target_input)
                    target_id = target_user.id
                target_name = target_user.first_name
                if target_user.username:
                    target_name = f"@{target_user.username}"
            except:
                await event.edit(f"❌ Kullanıcı bulunamadı: `{target_input}`")
                return
        else:
            await event.edit("❌ **Kullanım:**\n`.whisper @kullanıcı mesaj`\nveya yanıt vererek: `.whisper mesaj`")
            return
        
        if not target_id:
            await event.edit("❌ Hedef kullanıcı belirlenemedi!")
            return
        
        sender_id = event.sender_id
        whisper_id = hashlib.md5(f"{sender_id}{target_id}{time.time()}".encode()).hexdigest()[:10]
        
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
                bot_me = await main.bot.get_me()
                results = await client.inline_query(bot_me.username, f"wh_{whisper_id}")
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
        await event.edit("""**🔐 Whisper Plugin**

**Kullanım:**
• `.whisper @kullanıcı mesaj`
• Yanıt vererek: `.whisper mesaj`

**Örnek:**
`.whisper @ahmet Gizli mesaj!`""")


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
