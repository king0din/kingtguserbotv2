#Bu Plugin Sevgilinize, Eşinize, Dostunuza Atabilmeniz için
# @geceninefendisi Tarafından Geliştirildi!

import asyncio

from telethon import events
from collections import deque

from userbot import CMD_HELP, bot
from userbot.events import register

@register(outgoing=True, pattern="^.loveyou")
async def love(event):
    if event.fwd_from:
        return
    animation_interval = 0.5
    animation_ttl = range(0, 5)
    await event.edit("Seni Seviyorum")
    animation_chars = [
            "╔══╗╔╗ ♡ ♡ ♡",
            "╔══╗╔╗ ♡ ♡ ♡\n╚╗╔╝║║╔═╦╦╦╔╗",
            "╔══╗╔╗ ♡ ♡ ♡\n╚╗╔╝║║╔═╦╦╦╔╗\n╔╝╚╗║╚╣║║║║╔╣",
            "╔══╗╔╗ ♡ ♡ ♡\n╚╗╔╝║║╔═╦╦╦╔╗\n╔╝╚╗║╚╣║║║║╔╣\n╚══╝╚═╩═╩═╩═╝",
            "╔══╗╔╗ ♡ ♡ ♡\n╚╗╔╝║║╔═╦╦╦╔╗\n╔╝╚╗║╚╣║║║║╔╣\n╚══╝╚═╩═╩═╩═╝\nஜ۞ஜ YOU ஜ۞ஜ",

 ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i %5 ])