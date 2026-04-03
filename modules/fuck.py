# (c)@ryyu
"""Lütfen sadece .pinstall"""

from telethon import events

import asyncio

from userbot.events import register

@register(outgoing=True, pattern="^.fuck$")

async def bebe(event):

    if event.fwd_from:

        return

    animation_interval = 0.6

    animation_ttl = range(0, 9)

    await event.edit("FUCKK👧🏼")

    animation_chars = [
        
        "Annen sikildi🍆",
        "🧔🏻👩🏼❤️",
        "👙👙💅🏼💅🏼",
        "💏💏🔥",
        "💦💦💋💋💄👄",
        "👉🏼👉🏼👌🏼💦🔞🔞",
        "🚿🚿🛁🛁",
        "👨‍👩‍👧👨‍👩‍👧👪👧🏼👧🏼❤️❤️"
 ]

    for i in animation_ttl:

        await asyncio.sleep(animation_interval)

        await event.edit(animation_chars[i % 8])
