# modules/weather.py
# requires: requests, beautifulsoup4

from telethon import events
import requests
from bs4 import BeautifulSoup

def register(client):
    """Hava durumu modülü"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.hava (.+)'))
    async def weather_handler(event):
        city = event.pattern_match.group(1)
        await event.edit(f"🌤️ {city} için hava durumu aranıyor...")
        
        try:
            # Basit API çağrısı örneği
            response = requests.get(f"https://wttr.in/{city}?format=4", timeout=5)
            if response.status_code == 200:
                await event.edit(f"🌤️ **Hava Durumu**\n\n{response.text}")
            else:
                await event.edit(f"❌ Hava durumu bulunamadı")
        except Exception as e:
            await event.edit(f"❌ Hata: {str(e)}")
    
    print("[weather.py] Event handler'lar kaydedildi")
