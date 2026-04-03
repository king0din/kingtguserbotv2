# (c)@Rooternobody
"""Lütfen sadece .pinstall"""

from telethon import events

import asyncio

from userbot.events import register

@register(outgoing=True, pattern="^.sihir$")

async def matematiksihiri(event):

    if event.fwd_from:

        return

    animation_interval = 2.8

    animation_ttl = range(0, 13)

    await event.edit("Her işlem için 2.5 saniyen var.\nHızlı olmasın..")

    animation_chars = [
        
            "1’le 100 arasında aklından bir sayı tut.|⏳|",
            "1’le 100 arasında aklından bir sayı tut.|⌛|",
            "2 ile çarp.|⏳|",
            "2 ile çarp.|⌛|",
            "22'de al Asena’dan.|⏳|",
            "22'de al Asena’dan.|⌛|",
            "İkiye böl.|⏳|",
            "İkiye böl.|⌛|",
            "Şimdi aklından ilk tuttuğun sayıyı,\n bu son sayımızdan çıkar.|⏳|",
            "Şimdi aklından ilk tuttuğun sayıyı,\n bu son sayımızdan çıkar.|⌛|",
            "Şimdi sonucunu tahmin edicem.",
            "Sonuç tahmin ediliyor...",
            "|Sonuç:🔥11🔥|"
 ]

    for i in animation_ttl:

        await asyncio.sleep(animation_interval)

        await event.edit(animation_chars[i % 13])
