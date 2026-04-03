# (c)@mertimsii
"""neden bunu yaptim bilmiyorum"""

from telethon import events

import asyncio

from userbot.events import register

@register(outgoing=True, pattern="^.komikmis")

async def komik(event):

    if event.fwd_from:

        return

    animation_interval = 1.5

    animation_ttl = range(0, 17)

    await event.edit(" hahaha çok komik aq ")

    animation_chars = [
        
            "hahaha oğlum çok komik espri lan valla yemin ediyom.",
            "baya komik çok üst düzey bir espri bu ya.",
            "bunun düzeyini millet de öğrenmesi lazım.",
            "fazla komik yani, hani mesela bazı espriler yapıyorlar kanka bu kadar komik değil.",
            "hahaha",
            "ben şimdi buna gülüyorum ya, yarın gülemiycem diye üzülecem kendim. ",
            "hahaha ", 
            "ulan biraz az komik yap da gülmekten altıma sıçmayım",
            "hahaha",
            "sen bu espriyi bi tane uçak kirala, ",
            "arkasına koy bu espriyi, yedi düvel duysun bunu. ",
            "ulan gülmekten öldüm yemin ediyom bu kadar komik aaa. ",
            "yani biraz az komiğini yap bunun, gene gülecem",
            "çıkalım dağların başına hep beraber halay çekerek bu espriye gülelim, ",
            "yani bu esprinin karşılığı çok daha kaliteli esprilerin önünü de açar,",
            "ülke olarak kalkınırız yani.  ", 
            "sen bu espriyi yap afrikadaki çocuklar açlıktan ölmesin..",
 ]

    for i in animation_ttl:

        await asyncio.sleep(animation_interval)

        await event.edit(animation_chars[i % 17])
