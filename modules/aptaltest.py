# KingTG UserBot için uyumlu plugin
# Orijinal: @jefersonnX

from telethon import events
import asyncio
import random

def register(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.aptaltest (.+)'))
    async def aptaltest(event):
        u_name = event.pattern_match.group(1)
        
        await event.edit(f"🔍 **{u_name}** adlı kişinin ne kadar aptal olduğu araştırılıyor...")
        
        donus = random.randint(15, 40)
        sayi = 0
        
        await asyncio.sleep(0.3)
        for i in range(0, donus):
            await asyncio.sleep(0.1)
            sayi = random.randint(1, 100)
        
        await asyncio.sleep(0.1)
        await event.edit(f"🧠 **{u_name}** adlı kişinin **%{sayi}** aptal olduğu tespit edildi!")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.aptaltest$'))
    async def aptaltest_help(event):
        await event.edit("⚠️ **Kullanım:** `.aptaltest <isim>`\n\n**Örnek:** `.aptaltest Mustafa`")