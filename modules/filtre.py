# KingTG UserBot - Filtre Plugin
# Otomatik yanıt filtreleri
# Kullanım: .filtre <kelime> <yanıt> veya .filtreler

import os
import json
import random
from telethon import events
from userbot.events import register
from userbot import CMD_HELP

try:
    from userbot import TEMP_DOWNLOAD_DIRECTORY
except ImportError:
    TEMP_DOWNLOAD_DIRECTORY = "./downloads/"
    if not os.path.exists(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

# Filtre dosyası
FILTERS_FILE = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "filters.json")

# Filtreler {chat_id: {kelime: [yanıt1, yanıt2, ...]}}
# "global" key'i tüm sohbetlerde çalışır
FILTERS = {}


def load_filters():
    """Filtreleri dosyadan yükle"""
    global FILTERS
    try:
        if os.path.exists(FILTERS_FILE):
            with open(FILTERS_FILE, "r", encoding="utf-8") as f:
                FILTERS = json.load(f)
    except:
        FILTERS = {}
    
    # Global key yoksa oluştur
    if "global" not in FILTERS:
        FILTERS["global"] = {}


def save_filters():
    """Filtreleri dosyaya kaydet"""
    try:
        with open(FILTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(FILTERS, f, ensure_ascii=False, indent=2)
    except:
        pass


# Başlangıçta yükle
load_filters()


@register(outgoing=True, pattern=r"^\.filtre(?:\s+(.+))?$")
async def add_filter(event):
    """Filtre ekle"""
    if event.fwd_from:
        return
    
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    
    if not args:
        await event.edit(
            "**🔖 Filtre Plugin**\n\n"
            "**Sohbete Özel:**\n"
            "`.filtre <kelime> <yanıt>` - Filtre ekle\n"
            "`.filtre <kelime>` + yanıt - Yanıtı filtre olarak ekle\n"
            "`.filtreler` - Filtreleri göster\n"
            "`.fsil <kelime>` - Filtre sil\n\n"
            "**Global (Tüm Sohbetler):**\n"
            "`.gfiltre <kelime> <yanıt>` - Global filtre ekle\n"
            "`.gfiltre <kelime>` + yanıt - Yanıtı global filtre olarak ekle\n"
            "`.gfiltreler` - Global filtreleri göster\n"
            "`.gfsil <kelime>` - Global filtre sil\n\n"
            "**Diğer:**\n"
            "`.fgöster <kelime>` - Yanıtları göster\n"
            "`.ftemizle` - Tüm filtreleri sil\n\n"
            "**Örnek:**\n"
            "`.filtre king efendim` - Sadece bu sohbet\n"
            "`.gfiltre king efendim` - Tüm sohbetler\n"
            "Mesajı yanıtla + `.filtre king` - Yanıtı filtre yap"
        )
        return
    
    parts = args.split(None, 1)
    keyword = parts[0].lower().strip()
    
    # Yanıt varsa ve sadece kelime yazılmışsa, yanıtı response olarak al
    if reply and len(parts) == 1:
        if reply.text:
            response = reply.text.strip()
        elif reply.media:
            await event.edit("`❌ Şimdilik sadece metin yanıtlar destekleniyor!`")
            return
        else:
            await event.edit("`❌ Yanıtlanan mesajda metin yok!`")
            return
    elif len(parts) >= 2:
        response = parts[1].strip()
    else:
        await event.edit("`❌ Kullanım: .filtre <kelime> <yanıt>` veya mesajı yanıtla + `.filtre <kelime>`")
        return
    
    if not keyword or not response:
        await event.edit("`❌ Kelime ve yanıt boş olamaz!`")
        return
    
    chat_id = str(event.chat_id)
    
    # Chat için filtre dict oluştur
    if chat_id not in FILTERS:
        FILTERS[chat_id] = {}
    
    # Kelime için yanıt listesi oluştur veya ekle
    if keyword not in FILTERS[chat_id]:
        FILTERS[chat_id][keyword] = []
    
    # Aynı yanıt varsa ekleme
    if response in FILTERS[chat_id][keyword]:
        await event.edit(f"`⚠️ Bu yanıt zaten ekli: {keyword}`")
        return
    
    FILTERS[chat_id][keyword].append(response)
    save_filters()
    
    count = len(FILTERS[chat_id][keyword])
    response_short = response[:50] + "..." if len(response) > 50 else response
    await event.edit(f"`✅ Filtre eklendi!`\n\n`🔑 Kelime:` **{keyword}**\n`💬 Yanıt:` {response_short}\n`📊 Toplam yanıt:` {count}")


@register(outgoing=True, pattern=r"^\.filtreler$")
async def list_filters(event):
    """Filtreleri listele"""
    if event.fwd_from:
        return
    
    chat_id = str(event.chat_id)
    
    if chat_id not in FILTERS or not FILTERS[chat_id]:
        await event.edit("`📭 Bu sohbette filtre yok!`")
        return
    
    text = "**🔖 Bu Sohbetteki Filtreler:**\n\n"
    
    for keyword, responses in FILTERS[chat_id].items():
        text += f"**🔑 {keyword}** ({len(responses)} yanıt)\n"
        for i, resp in enumerate(responses[:3], 1):  # İlk 3 yanıtı göster
            resp_short = resp[:30] + "..." if len(resp) > 30 else resp
            text += f"  `{i}.` {resp_short}\n"
        if len(responses) > 3:
            text += f"  _... ve {len(responses) - 3} yanıt daha_\n"
        text += "\n"
    
    await event.edit(text)


@register(outgoing=True, pattern=r"^\.fgöster(?:\s+(.+))?$")
async def show_filter(event):
    """Belirli bir filtrenin tüm yanıtlarını göster"""
    if event.fwd_from:
        return
    
    keyword = event.pattern_match.group(1)
    
    if not keyword:
        await event.edit("`❌ Kullanım: .fgöster <kelime>`")
        return
    
    keyword = keyword.lower().strip()
    chat_id = str(event.chat_id)
    
    if chat_id not in FILTERS or keyword not in FILTERS[chat_id]:
        await event.edit(f"`❌ Filtre bulunamadı: {keyword}`")
        return
    
    responses = FILTERS[chat_id][keyword]
    
    text = f"**🔖 Filtre: {keyword}**\n\n"
    for i, resp in enumerate(responses, 1):
        text += f"`{i}.` {resp}\n"
    
    text += f"\n`📊 Toplam:` {len(responses)} yanıt"
    
    await event.edit(text)


@register(outgoing=True, pattern=r"^\.fsil(?:\s+(.+))?$")
async def delete_filter(event):
    """Filtre sil"""
    if event.fwd_from:
        return
    
    args = event.pattern_match.group(1)
    
    if not args:
        await event.edit("`❌ Kullanım: .fsil <kelime>` veya `.fsil <kelime> <numara>`")
        return
    
    parts = args.split()
    keyword = parts[0].lower().strip()
    
    chat_id = str(event.chat_id)
    
    if chat_id not in FILTERS or keyword not in FILTERS[chat_id]:
        await event.edit(f"`❌ Filtre bulunamadı: {keyword}`")
        return
    
    # Numara verilmişse sadece o yanıtı sil
    if len(parts) > 1 and parts[1].isdigit():
        index = int(parts[1]) - 1
        if 0 <= index < len(FILTERS[chat_id][keyword]):
            removed = FILTERS[chat_id][keyword].pop(index)
            
            # Yanıt kalmadıysa kelimeyi de sil
            if not FILTERS[chat_id][keyword]:
                del FILTERS[chat_id][keyword]
                await event.edit(f"`✅ Son yanıt silindi, filtre kaldırıldı: {keyword}`")
            else:
                save_filters()
                await event.edit(f"`✅ Yanıt silindi!`\n`🔑` **{keyword}**\n`❌` {removed[:50]}...")
            
            save_filters()
            return
        else:
            await event.edit(f"`❌ Geçersiz numara! (1-{len(FILTERS[chat_id][keyword])})`")
            return
    
    # Tüm filtreyi sil
    del FILTERS[chat_id][keyword]
    save_filters()
    
    await event.edit(f"`✅ Filtre silindi: {keyword}`")


@register(outgoing=True, pattern=r"^\.ftemizle$")
async def clear_filters(event):
    """Tüm filtreleri sil"""
    if event.fwd_from:
        return
    
    chat_id = str(event.chat_id)
    
    if chat_id not in FILTERS or not FILTERS[chat_id]:
        await event.edit("`📭 Silinecek filtre yok!`")
        return
    
    count = len(FILTERS[chat_id])
    del FILTERS[chat_id]
    save_filters()
    
    await event.edit(f"`✅ {count} filtre silindi!`")


@register(outgoing=True, pattern=r"^\.fglobal$")
async def global_filters(event):
    """Tüm sohbetlerdeki filtreleri göster"""
    if event.fwd_from:
        return
    
    if not FILTERS:
        await event.edit("`📭 Hiç filtre yok!`")
        return
    
    text = "**🌐 Tüm Filtreler:**\n\n"
    
    total = 0
    for chat_id, filters in FILTERS.items():
        if filters:
            if chat_id == "global":
                text += f"**🌍 GLOBAL:**\n"
            else:
                text += f"**📍 Chat {chat_id}:**\n"
            for keyword in filters.keys():
                text += f"  • {keyword} ({len(filters[keyword])} yanıt)\n"
                total += 1
            text += "\n"
    
    text += f"`📊 Toplam:` {total} filtre"
    
    await event.edit(text)


@register(outgoing=True, pattern=r"^\.gfiltre(?:\s+(.+))?$")
async def add_global_filter(event):
    """Global filtre ekle - tüm sohbetlerde çalışır"""
    if event.fwd_from:
        return
    
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    
    if not args:
        await event.edit("`❌ Kullanım: .gfiltre <kelime> <yanıt>` veya mesajı yanıtla + `.gfiltre <kelime>`")
        return
    
    parts = args.split(None, 1)
    keyword = parts[0].lower().strip()
    
    # Yanıt varsa ve sadece kelime yazılmışsa, yanıtı response olarak al
    if reply and len(parts) == 1:
        if reply.text:
            response = reply.text.strip()
        elif reply.media:
            await event.edit("`❌ Şimdilik sadece metin yanıtlar destekleniyor!`")
            return
        else:
            await event.edit("`❌ Yanıtlanan mesajda metin yok!`")
            return
    elif len(parts) >= 2:
        response = parts[1].strip()
    else:
        await event.edit("`❌ Kullanım: .gfiltre <kelime> <yanıt>` veya mesajı yanıtla + `.gfiltre <kelime>`")
        return
    
    if not keyword or not response:
        await event.edit("`❌ Kelime ve yanıt boş olamaz!`")
        return
    
    # Global filtre dict oluştur
    if "global" not in FILTERS:
        FILTERS["global"] = {}
    
    if keyword not in FILTERS["global"]:
        FILTERS["global"][keyword] = []
    
    if response in FILTERS["global"][keyword]:
        await event.edit(f"`⚠️ Bu yanıt zaten ekli: {keyword}`")
        return
    
    FILTERS["global"][keyword].append(response)
    save_filters()
    
    count = len(FILTERS["global"][keyword])
    response_short = response[:50] + "..." if len(response) > 50 else response
    await event.edit(f"`✅ Global filtre eklendi!`\n\n`🔑 Kelime:` **{keyword}**\n`💬 Yanıt:` {response_short}\n`📊 Toplam yanıt:` {count}\n\n`🌍 Tüm sohbetlerde aktif!`")


@register(outgoing=True, pattern=r"^\.gfiltreler$")
async def list_global_filters(event):
    """Global filtreleri listele"""
    if event.fwd_from:
        return
    
    if "global" not in FILTERS or not FILTERS["global"]:
        await event.edit("`📭 Global filtre yok!`")
        return
    
    text = "**🌍 Global Filtreler:**\n_(Tüm sohbetlerde aktif)_\n\n"
    
    for keyword, responses in FILTERS["global"].items():
        text += f"**🔑 {keyword}** ({len(responses)} yanıt)\n"
        for i, resp in enumerate(responses[:3], 1):
            resp_short = resp[:30] + "..." if len(resp) > 30 else resp
            text += f"  `{i}.` {resp_short}\n"
        if len(responses) > 3:
            text += f"  _... ve {len(responses) - 3} yanıt daha_\n"
        text += "\n"
    
    await event.edit(text)


@register(outgoing=True, pattern=r"^\.gfsil(?:\s+(.+))?$")
async def delete_global_filter(event):
    """Global filtre sil"""
    if event.fwd_from:
        return
    
    args = event.pattern_match.group(1)
    
    if not args:
        await event.edit("`❌ Kullanım: .gfsil <kelime>` veya `.gfsil <kelime> <numara>`")
        return
    
    parts = args.split()
    keyword = parts[0].lower().strip()
    
    if "global" not in FILTERS or keyword not in FILTERS["global"]:
        await event.edit(f"`❌ Global filtre bulunamadı: {keyword}`")
        return
    
    # Numara verilmişse sadece o yanıtı sil
    if len(parts) > 1 and parts[1].isdigit():
        index = int(parts[1]) - 1
        if 0 <= index < len(FILTERS["global"][keyword]):
            removed = FILTERS["global"][keyword].pop(index)
            
            if not FILTERS["global"][keyword]:
                del FILTERS["global"][keyword]
                await event.edit(f"`✅ Son yanıt silindi, global filtre kaldırıldı: {keyword}`")
            else:
                await event.edit(f"`✅ Global yanıt silindi!`\n`🔑` **{keyword}**\n`❌` {removed[:50]}...")
            
            save_filters()
            return
        else:
            await event.edit(f"`❌ Geçersiz numara! (1-{len(FILTERS['global'][keyword])})`")
            return
    
    # Tüm filtreyi sil
    del FILTERS["global"][keyword]
    save_filters()
    
    await event.edit(f"`✅ Global filtre silindi: {keyword}`")


@register(outgoing=True, pattern=r"^\.gfgöster(?:\s+(.+))?$")
async def show_global_filter(event):
    """Global filtrenin tüm yanıtlarını göster"""
    if event.fwd_from:
        return
    
    keyword = event.pattern_match.group(1)
    
    if not keyword:
        await event.edit("`❌ Kullanım: .gfgöster <kelime>`")
        return
    
    keyword = keyword.lower().strip()
    
    if "global" not in FILTERS or keyword not in FILTERS["global"]:
        await event.edit(f"`❌ Global filtre bulunamadı: {keyword}`")
        return
    
    responses = FILTERS["global"][keyword]
    
    text = f"**🌍 Global Filtre: {keyword}**\n\n"
    for i, resp in enumerate(responses, 1):
        text += f"`{i}.` {resp}\n"
    
    text += f"\n`📊 Toplam:` {len(responses)} yanıt"
    
    await event.edit(text)


# Gelen mesajları dinle
@register(incoming=True)
async def filter_listener(event):
    """Gelen mesajları filtrele ve yanıtla"""
    if not event.text:
        return
    
    chat_id = str(event.chat_id)
    message_text = event.text.lower()
    
    # Önce sohbete özel filtreleri kontrol et
    if chat_id in FILTERS and FILTERS[chat_id]:
        for keyword, responses in FILTERS[chat_id].items():
            if keyword in message_text:
                response = random.choice(responses)
                await event.reply(response)
                return  # İlk eşleşmede dur
    
    # Sonra global filtreleri kontrol et
    if "global" in FILTERS and FILTERS["global"]:
        for keyword, responses in FILTERS["global"].items():
            if keyword in message_text:
                response = random.choice(responses)
                await event.reply(response)
                return  # İlk eşleşmede dur


CMD_HELP.update({
    "filtre":
    "**Sohbete Özel:**\n"
    "`.filtre <kelime> <yanıt>` - Filtre ekle\n"
    "`.filtreler` - Filtreleri göster\n"
    "`.fgöster <kelime>` - Yanıtları göster\n"
    "`.fsil <kelime>` - Filtre sil\n"
    "`.fsil <kelime> <no>` - Belirli yanıtı sil\n"
    "`.ftemizle` - Tüm filtreleri sil\n\n"
    "**Global (Tüm Sohbetler):**\n"
    "`.gfiltre <kelime> <yanıt>` - Global filtre ekle\n"
    "`.gfiltreler` - Global filtreleri göster\n"
    "`.gfgöster <kelime>` - Global yanıtları göster\n"
    "`.gfsil <kelime>` - Global filtre sil\n\n"
    "`.fglobal` - Tüm filtreleri göster"
})