################################
# Coded By Yusuf Usta [@Fusuf] #
#        @AsenaUserBot         #
#             2020             #
################################

from userbot.events import register
from PIL import Image
from asyncio import sleep

@register(outgoing=True, pattern="^.hipnoz ?(\d*)")
async def hipnoz(event):
    sayi = event.pattern_match.group(1)
    if not sayi:
        sayi = 20
    else:
        sayi = int(sayi)

    cap1 = "`°º¤ø,¸¸,ø¤º°`°º¤ø,¸`\n**Hipnoz Oluyorsun**\n`¸,ø¤º°`°º¤ø,¸¸,ø¤º°`"
    cap2 = "`¸,ø¤º°`°º¤ø,¸¸,ø¤º°`\n**Hipnoz Oluyorsun** \n`°º¤ø,¸¸,ø¤º°`°º¤ø,`"

    siyah = Image.new("RGB", (512, 512), "#000000")
    siyah.save("siyah.png", 'PNG')

    beyaz = Image.new("RGB", (512, 512), "#ffffff")
    beyaz.save("beyaz.png", 'PNG')

    await event.delete()
    dongu = [("beyaz.png"), ("siyah.png")] * sayi
    mesaj = await event.client.send_file(event.chat_id, "siyah.png", caption=cap1)

    for foto in dongu:
        await sleep(0.3)
        if foto == "beyaz.png":
            await mesaj.edit(cap2, file=foto)
        else:
            await mesaj.edit(cap1, file=foto)

    await mesaj.edit("**Haha Hipnoz Oldun 😳**")