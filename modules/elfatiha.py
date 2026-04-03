# (c)@TurcoCerveza & @ereeennn
"""Bir İman sonucudur.."""

from telethon import events
import asyncio
from userbot.events import register

@register(outgoing=True, pattern="^.fatiha")
async def fatiha(event):
    if event.fwd_from:
        return

    animation_interval = 1.0
    animation_ttl = range(0, 12)
    await event.edit("Bismillahirrahmanirrahim")
    animation_chars = ["_🕌_", "Elhamdulillâhi Rabbi’l-âlemîn.", "_🕌_", "Er-Rahmâni’r-Rahîm", "_🕌_", "Mâliki yevmi’d-dîn.", "_🕌_", "İyyâke na’budu ve iyyâke neste’în.", "_🕌_", "İhdine’s-sırata’l-mustakim.", "_🕌_", "Sırata’l-lezîne en’amte aleyhim. Ğayri’l-meğdubi aleyhim ve le’d-dallîn."]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 12])
