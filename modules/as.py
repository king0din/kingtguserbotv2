# (c)@Rooternobody
"""Lütfen sadece .pinstall"""

from telethon import events

import asyncio

from userbot.events import register

@register(outgoing=True, pattern="^as$")

async def merkurkedissa(event):

    if event.fwd_from:

        return

    animation_interval = 0.4

    animation_ttl = range(0, 9)

    await event.edit("Aleyküm selam..🐉")

    animation_chars = [
        
            "A",
            "As",
            "A ve S",
            "🎃ase",
            "🍻hoşgeldin",
            "💐As",
            "🍁sana da Selammm",
            "💥Nabere",
            "**🔥Ase**"

 ]

    for i in animation_ttl:

        await asyncio.sleep(animation_interval)

        await event.edit(animation_chars[i % 9])
