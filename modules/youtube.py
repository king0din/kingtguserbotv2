# KingTG UserBot - YouTube İndirme Plugin
# YouTube'dan müzik ve video indir
# Kullanım: .müzik <şarkı adı/link> veya .video <video adı/link>

import os
import re
import asyncio
from telethon import events
from userbot.events import register
from userbot import CMD_HELP

try:
    from userbot import TEMP_DOWNLOAD_DIRECTORY
except ImportError:
    TEMP_DOWNLOAD_DIRECTORY = "./downloads/"
    if not os.path.exists(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)

# YouTube link regex
YT_REGEX = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'


def is_youtube_url(text):
    return bool(re.match(YT_REGEX, text))


async def run_command(cmd):
    """Shell komutu çalıştır"""
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode(), process.returncode


async def get_video_info(query):
    """Video bilgilerini al"""
    if is_youtube_url(query):
        url = query
    else:
        # Arama yap
        search_cmd = f'yt-dlp "ytsearch1:{query}" --get-id --get-title --no-warnings'
        stdout, stderr, code = await run_command(search_cmd)
        
        if code != 0 or not stdout.strip():
            return None, None, None
        
        lines = stdout.strip().split('\n')
        if len(lines) >= 2:
            title = lines[0]
            video_id = lines[1]
            url = f"https://www.youtube.com/watch?v={video_id}"
            return url, title, video_id
        return None, None, None
    
    # URL'den bilgi al
    info_cmd = f'yt-dlp "{url}" --get-title --get-id --no-warnings'
    stdout, stderr, code = await run_command(info_cmd)
    
    if code != 0 or not stdout.strip():
        return url, None, None
    
    lines = stdout.strip().split('\n')
    title = lines[0] if lines else None
    video_id = lines[1] if len(lines) > 1 else None
    
    return url, title, video_id


async def download_audio(url, output_dir):
    """Ses indir"""
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    cmd = f'yt-dlp -x --audio-format mp3 --audio-quality 0 -o "{output_template}" "{url}" --no-warnings --no-playlist'
    
    stdout, stderr, code = await run_command(cmd)
    
    if code != 0:
        return None, stderr
    
    # İndirilen dosyayı bul
    for f in os.listdir(output_dir):
        if f.endswith('.mp3'):
            return os.path.join(output_dir, f), None
    
    return None, "Dosya bulunamadı"


async def download_video(url, output_dir, quality="best"):
    """Video indir"""
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    # 720p veya daha düşük kalite (Telegram limiti için)
    cmd = f'yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" --merge-output-format mp4 -o "{output_template}" "{url}" --no-warnings --no-playlist'
    
    stdout, stderr, code = await run_command(cmd)
    
    if code != 0:
        # Alternatif format dene
        cmd = f'yt-dlp -f "best[height<=720]" -o "{output_template}" "{url}" --no-warnings --no-playlist'
        stdout, stderr, code = await run_command(cmd)
        
        if code != 0:
            return None, stderr
    
    # İndirilen dosyayı bul
    for f in os.listdir(output_dir):
        if f.endswith(('.mp4', '.mkv', '.webm')):
            return os.path.join(output_dir, f), None
    
    return None, "Dosya bulunamadı"


def clean_dir(directory):
    """Klasörü temizle"""
    for f in os.listdir(directory):
        try:
            os.remove(os.path.join(directory, f))
        except:
            pass


def format_size(size_bytes):
    """Dosya boyutunu formatla"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@register(outgoing=True, pattern=r"^\.m[uü]zik(?:\s+(.+))?$")
async def music_download(event):
    if event.fwd_from:
        return
    
    query = event.pattern_match.group(1)
    
    if not query:
        await event.edit(
            "**🎵 YouTube Müzik İndirme**\n\n"
            "**Kullanım:**\n"
            "`.müzik <şarkı adı>` - Arama yaparak indir\n"
            "`.müzik <youtube linki>` - Direkt indir\n\n"
            "**Örnek:**\n"
            "`.müzik duman senden daha güzel`\n"
            "`.müzik https://youtu.be/xxxxx`"
        )
        return
    
    await event.edit(f"`🔍 Aranıyor: {query}`")
    
    # Video bilgilerini al
    url, title, video_id = await get_video_info(query)
    
    if not url:
        await event.edit("`❌ Video bulunamadı!`")
        return
    
    title_display = title[:50] + "..." if title and len(title) > 50 else (title or "Bilinmeyen")
    await event.edit(f"`🎵 İndiriliyor: {title_display}`")
    
    # İndirme klasörü
    dl_dir = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "yt_music")
    if not os.path.exists(dl_dir):
        os.makedirs(dl_dir)
    clean_dir(dl_dir)
    
    # İndir
    file_path, error = await download_audio(url, dl_dir)
    
    if not file_path or not os.path.exists(file_path):
        await event.edit(f"`❌ İndirme hatası: {error or 'Bilinmeyen hata'}`")
        return
    
    # Dosya boyutunu kontrol et
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:  # 50 MB
        await event.edit("`❌ Dosya çok büyük (>50MB)!`")
        clean_dir(dl_dir)
        return
    
    await event.edit(f"`📤 Gönderiliyor: {format_size(file_size)}`")
    
    # Gönder
    try:
        await event.client.send_file(
            event.chat_id,
            file_path,
            caption=f"🎵 **{title or 'Müzik'}**\n\n`{url}`",
            attributes=[],
            force_document=False
        )
        await event.delete()
    except Exception as e:
        await event.edit(f"`❌ Gönderme hatası: {e}`")
    finally:
        clean_dir(dl_dir)


@register(outgoing=True, pattern=r"^\.video(?:\s+(.+))?$")
async def video_download(event):
    if event.fwd_from:
        return
    
    query = event.pattern_match.group(1)
    
    if not query:
        await event.edit(
            "**🎬 YouTube Video İndirme**\n\n"
            "**Kullanım:**\n"
            "`.video <video adı>` - Arama yaparak indir\n"
            "`.video <youtube linki>` - Direkt indir\n\n"
            "**Örnek:**\n"
            "`.video duman senden daha güzel klip`\n"
            "`.video https://youtu.be/xxxxx`"
        )
        return
    
    await event.edit(f"`🔍 Aranıyor: {query}`")
    
    # Video bilgilerini al
    url, title, video_id = await get_video_info(query)
    
    if not url:
        await event.edit("`❌ Video bulunamadı!`")
        return
    
    title_display = title[:50] + "..." if title and len(title) > 50 else (title or "Bilinmeyen")
    await event.edit(f"`🎬 İndiriliyor: {title_display}`")
    
    # İndirme klasörü
    dl_dir = os.path.join(TEMP_DOWNLOAD_DIRECTORY, "yt_video")
    if not os.path.exists(dl_dir):
        os.makedirs(dl_dir)
    clean_dir(dl_dir)
    
    # İndir
    file_path, error = await download_video(url, dl_dir)
    
    if not file_path or not os.path.exists(file_path):
        await event.edit(f"`❌ İndirme hatası: {error or 'Bilinmeyen hata'}`")
        return
    
    # Dosya boyutunu kontrol et
    file_size = os.path.getsize(file_path)
    if file_size > 2000 * 1024 * 1024:  # 2 GB (Telegram premium limiti)
        await event.edit("`❌ Dosya çok büyük (>2GB)!`")
        clean_dir(dl_dir)
        return
    
    await event.edit(f"`📤 Gönderiliyor: {format_size(file_size)}`")
    
    # Gönder
    try:
        await event.client.send_file(
            event.chat_id,
            file_path,
            caption=f"🎬 **{title or 'Video'}**\n\n`{url}`",
            supports_streaming=True
        )
        await event.delete()
    except Exception as e:
        await event.edit(f"`❌ Gönderme hatası: {e}`")
    finally:
        clean_dir(dl_dir)


@register(outgoing=True, pattern=r"^\.ytara(?:\s+(.+))?$")
async def yt_search(event):
    """YouTube'da arama yap"""
    if event.fwd_from:
        return
    
    query = event.pattern_match.group(1)
    
    if not query:
        await event.edit("`❌ Aranacak şeyi yaz: .ytara <sorgu>`")
        return
    
    await event.edit(f"`🔍 Aranıyor: {query}`")
    
    # 5 sonuç al
    cmd = f'yt-dlp "ytsearch5:{query}" --get-id --get-title --get-duration --no-warnings'
    stdout, stderr, code = await run_command(cmd)
    
    if code != 0 or not stdout.strip():
        await event.edit("`❌ Sonuç bulunamadı!`")
        return
    
    lines = stdout.strip().split('\n')
    results = []
    
    i = 0
    count = 1
    while i < len(lines) and count <= 5:
        if i + 2 < len(lines):
            title = lines[i]
            video_id = lines[i + 1]
            duration = lines[i + 2] if i + 2 < len(lines) else "?"
            
            # Süreyi formatla
            try:
                dur_int = int(duration)
                mins = dur_int // 60
                secs = dur_int % 60
                duration = f"{mins}:{secs:02d}"
            except:
                duration = "?"
            
            url = f"https://youtu.be/{video_id}"
            title_short = title[:40] + "..." if len(title) > 40 else title
            results.append(f"`{count}.` [{title_short}]({url}) `({duration})`")
            count += 1
            i += 3
        else:
            break
    
    if results:
        text = f"**🔍 YouTube Arama: {query}**\n\n" + "\n".join(results)
        text += "\n\n_İndirmek için: `.müzik <link>` veya `.video <link>`_"
        await event.edit(text, link_preview=False)
    else:
        await event.edit("`❌ Sonuç bulunamadı!`")


CMD_HELP.update({
    "youtube":
    "`.müzik <şarkı/link>` - YouTube'dan MP3 indir\n"
    "`.video <video/link>` - YouTube'dan video indir\n"
    "`.ytara <sorgu>` - YouTube'da arama yap"
})