"""Emoji
Available Commands:
.emoji shrug
.emoji apple
.emoji :/
.emoji -_-"""

from telethon import events

import asyncio
from userbot.events import register

@register(outgoing=True, pattern="^.bira")

async def bira(event):
    if event.fwd_from:
        return
    animation_interval = 0.1
    animation_ttl = range(0, 101)
    animation_chars = [
            "🍺       🍺",
            "🍺     🍺",
            "🍺  🍺",
            "🍻"
    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 4])