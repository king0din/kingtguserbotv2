# modules/selam.py
from telethon import events
import asyncio

def register(client):
    """Ana bot client'ını alıp event'leri kaydet"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.selam$'))
    async def selam_animasyon(event):
        animasyon = [
            "👋",
            "👋 S",
            "👋 Se",
            "👋 Sel",
            "👋 Sela",
            "👋 Selam!",
        ]
        
        for frame in animasyon:
            await event.edit(frame)
            await asyncio.sleep(0.3)
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.merhaba$'))
    async def merhaba(event):
        await event.edit("👋 Merhaba dünya!")
    
    print("[selam.py] Event handler'lar kaydedildi")
