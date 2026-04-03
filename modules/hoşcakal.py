from telethon import events
import asyncio
from userbot.events import register 

@register(outgoing=True, pattern="^.bb")
async def komut_testx(event):
    ANIMASYON = ["Hoşcakalın🌹" ,"Görüşürüz🌚", "Belki gelirim...", "Belki gelmem🐭", "Yinede unutmayın beni😜", "Boş yaptım 🥴", "Hadi bb"]
    for anim in ANIMASYON:
        await event.edit(anim)
        await asyncio.sleep(1.2)