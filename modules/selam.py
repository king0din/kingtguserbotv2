from telethon import events
import asyncio

# @events.register kullandığında, main.py içindeki "isinstance" bunu tanır.
@events.register(events.NewMessage(outgoing=True, pattern=r'\.sa'))
async def selam_animasyon(event):
    animasyon = ["S", "Se", "Sel", "Selam", "Selam Aleyküm!", "🌹"]
    for kare in animasyon:
        await event.edit(kare)
        await asyncio.sleep(0.5)
