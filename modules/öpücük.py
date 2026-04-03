# @Ardaggg tarafindan yapilmistir hdi eyw.

from telethon import events
import asyncio
from userbot.events import register

@register(outgoing=True, pattern="^.opucuk")
async def muahhh(event):
    if event.fwd_from:
        return
    animation_interval = 0.9
    animation_ttl = range(0, 4)
    await event.edit("kiss")
    animation_chars = [  
        "şşt",
        "öpem mi",
        "bak öpüom haa",
        "muaahhhh",
    ]

    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 4])