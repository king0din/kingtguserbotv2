#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#    Change the language for @Erdme

from userbot import CMD_HELP
from userbot.events import register

from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.utils import get_input_location
import asyncio


if 1 == 1:
    name = "Profil Fotoğrafları"
    client = "userbot"

@register(outgoing=True, pattern="^.poto(?: |$)(.*)", disable_errors=True)
async def potocmd(event):
    """Yanıtlanan kullanıcının ve ya grup/kanal'ın fotoğraflarını verir."""
    id = "".join(event.raw_text.split(maxsplit=2)[1:])
    user = await event.get_reply_message()
    chat = event.input_chat
    await event.edit(f"`İşleniyor........`")
    if user:
        photos = await event.client.get_profile_photos(user.sender)
        u = True
    else:
        photos = await event.client.get_profile_photos(chat)
        u = False
    if id.strip() == "":
        if len(photos) > 0:
            await event.client.send_file(event.chat_id, photos)
            await event.edit(f"`Fotoğraflar başarıyla yüklendi!`")
        else:
            try:
                if u is True:
                    photo = await event.client.download_profile_photo(user.sender)
                else:
                    photo = await event.client.download_profile_photo(event.input_chat)
                await event.client.send_file(event.chat_id, photo)
                await event.edit(f"`Fotoğraflar başarıyla yüklendi!`")
            except a:
                await event.edit("**Bu kullanıcının hiç fotoğrafı yok!**")
                return
    else:
        try:
            id = int(id)
            if id <= 0:
                await event.edit("`Lütfen birini yanıtlayın!`")
                return
        except:
            await event.edit(f"`Lütfen birini yanıtlayın!`")
            return
        if int(id) <= (len(photos)):
            send_photos = await event.client.download_media(photos[id - 1])
            await event.client.send_file(event.chat_id, send_photos)
        else:
            await event.edit(f"`Sanırım bu sohbette medya gönderme yetkim yok!`")
            await asyncio.sleep(8)
            return


CMD_HELP.update({
    "poto":
    ".poto <birini yanıtla>\
\nKullanım: Yanıtladığınız kişinin fotoğraflarını atar!\
\n.poto <sayı>\
\nKullanım: Yanıtladığınız birinin <sayı> fotoğrafını atar."
})
