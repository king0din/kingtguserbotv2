# (c)@jokerabiniz

"""Emoji

Available Commands:

muah$"""

from telethon import events

import asyncio

from userbot.events import register

@register(outgoing=True, pattern="^muah$")

async def oof(e):
    t = "muah"
    for j in range(16):
        t = t[:-1] + "ah"
        await e.edit(t)
        