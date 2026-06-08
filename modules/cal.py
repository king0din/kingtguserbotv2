import asyncio
import os
import logging
import time
import json
from telethon import events, Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeAudio
from telethon.tl.functions.channels import (
    JoinChannelRequest, GetParticipantRequest,
    GetFullChannelRequest, InviteToChannelRequest
)
from telethon.tl.functions.messages import (
    ImportChatInviteRequest, GetFullChatRequest, AddChatUserRequest
)
from telethon.tl.types import (
    ChannelParticipantAdmin, ChannelParticipantCreator,
    ChatAdminRights, Channel, Chat, ChannelForbidden,
    ChatParticipantAdmin, ChatParticipantCreator
)
from telethon.errors import (
    UserNotParticipantError, ChannelPrivateError,
    InviteHashExpiredError, UserAlreadyParticipantError,
    ChatAdminRequiredError, FloodWaitError, UserBannedInChannelError,
    UserNotMutualContactError, UserPrivacyRestrictedError
)

logging.basicConfig(level=logging.ERROR)

try:
    import yt_dlp
except:
    pass

try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream
    from pytgcalls.types import Update
    try:
        from pytgcalls.exceptions import (
            NoActiveGroupCall, GroupCallNotFound,
            AlreadyJoinedError, NotInGroupCallError
        )
    except ImportError:
        class NoActiveGroupCall(Exception): pass
        class GroupCallNotFound(Exception): pass
        class AlreadyJoinedError(Exception): pass
        class NotInGroupCallError(Exception): pass
except:
    pass

# ═══════════════════════════════════════════════════════════
#  AYARLAR
# ═══════════════════════════════════════════════════════════
DEFAULT_MUSIC_SESSION = "1BJWap1sBuzlsIh9jRJzHeFGHx7GiC-Por9cwTk8MisHFv6gxoUQXc5zGQz-KMTKyD6owZs_9FUoTMRYBd38hkZl8jQq4shETjkzVWZs2eUBgBjcpCv--pWztp8BNwC5UFpPWGva1U-6azdsyEHloPzhuJPvokYs10js--knr6GaeUV0nEOJ5cbBeqbi4l0Pfkqgxo_XjobMv9WenrsR7r1_l2Y0kOC_q6zSJZqcMmk8mbctqMqGCkqFTaTebOTVpIffVQHNNyumtriUzGN6rS4tCJXeYbN2zdY8i7PmfpmipfAdk8CseX-sUKZKS03EUh3F2ntgytzzqptbP1OPpZ3xDqe7lUEE="
MUSIC_SESSION = os.getenv("MUSIC_SESSION", DEFAULT_MUSIC_SESSION)
LOG_GROUP = -5027859960
OWNER_ID = None
PERMISSIONS_FILE = "music_permissions.json"

# ═══════════════════════════════════════════════════════════
#  GLOBAL DEĞİŞKENLER
# ═══════════════════════════════════════════════════════════
music_client = None
pytgcalls_client = None   # "pytgcalls" ismi global çakışmasın diye
userbot_client = None
bot_client = None
bot_username = None
handlers_registered = False

music_queues = {}
current_songs = {}
is_playing = {}
is_paused = {}
private_mode = {}
download_status = {}
download_tasks = {}
panel_update_tasks = {}
bot_in_group_cache = {}
assistant_status_cache = {}

BOT_CACHE_DURATION = 600
CACHE_DURATION = 300

# ═══════════════════════════════════════════════════════════
#  YETKİ SİSTEMİ
# ═══════════════════════════════════════════════════════════
permissions_data = {
    "allowed_users": [],
    "allowed_groups": [],
    "blocked_users": {}
}

def load_permissions():
    global permissions_data
    try:
        if os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, 'r') as f:
                permissions_data = json.load(f)
    except:
        pass

def save_permissions():
    try:
        with open(PERMISSIONS_FILE, 'w') as f:
            json.dump(permissions_data, f, indent=2)
    except:
        pass

def add_allowed_user(user_id):
    if user_id not in permissions_data["allowed_users"]:
        permissions_data["allowed_users"].append(user_id)
        save_permissions()
        return True
    return False

def remove_allowed_user(user_id):
    if user_id in permissions_data["allowed_users"]:
        permissions_data["allowed_users"].remove(user_id)
        save_permissions()
        return True
    return False

def add_allowed_group(group_id):
    if group_id not in permissions_data["allowed_groups"]:
        permissions_data["allowed_groups"].append(group_id)
        save_permissions()
        return True
    return False

def remove_allowed_group(group_id):
    if group_id in permissions_data["allowed_groups"]:
        permissions_data["allowed_groups"].remove(group_id)
        save_permissions()
        return True
    return False

def block_user_in_group(user_id, group_id):
    key = str(group_id)
    if key not in permissions_data["blocked_users"]:
        permissions_data["blocked_users"][key] = []
    if user_id not in permissions_data["blocked_users"][key]:
        permissions_data["blocked_users"][key].append(user_id)
        save_permissions()
        return True
    return False

def unblock_user_in_group(user_id, group_id):
    key = str(group_id)
    if key in permissions_data["blocked_users"]:
        if user_id in permissions_data["blocked_users"][key]:
            permissions_data["blocked_users"][key].remove(user_id)
            save_permissions()
            return True
    return False

def check_permission(user_id, group_id):
    if user_id == OWNER_ID:
        return True
    if not private_mode.get(group_id, False):
        return True
    key = str(group_id)
    if key in permissions_data["blocked_users"]:
        if user_id in permissions_data["blocked_users"][key]:
            return False
    if user_id in permissions_data["allowed_users"]:
        return True
    if group_id in permissions_data["allowed_groups"]:
        return True
    return False

load_permissions()

# ═══════════════════════════════════════════════════════════
#  YT-DLP AYARLARI
# ═══════════════════════════════════════════════════════════
YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'outtmpl': '/tmp/%(id)s.%(ext)s',
    'socket_timeout': 30,
    'retries': 3,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128'
    }]
}

# ═══════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════
def format_duration(seconds):
    if not seconds or seconds == 0:
        return "00:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def create_progress_bar(current, total, length=10):
    if total == 0:
        return "▓" * length
    filled = min(int(length * current / total), length)
    empty = length - filled
    return "▓" * filled + "░" * empty

def get_elapsed_time(chat_id):
    if chat_id not in current_songs or not current_songs[chat_id]:
        return 0
    song = current_songs[chat_id]
    started_at = song.get('started_at', time.time())
    if is_paused.get(chat_id, False):
        paused_at = song.get('paused_at', time.time())
        return paused_at - started_at
    return time.time() - started_at

async def get_audio_from_log(video_id):
    if not music_client or not music_client.is_connected():
        return None
    try:
        async for msg in music_client.iter_messages(LOG_GROUP, search=video_id, limit=1):
            if msg.audio or msg.document:
                return msg
    except:
        pass
    return None

# ═══════════════════════════════════════════════════════════
#  MESAJ GÖNDERİM
# ═══════════════════════════════════════════════════════════
async def send_message(chat_id, text, buttons=None, reply_to=None):
    global bot_client, userbot_client
    if await is_bot_in_group(chat_id):
        try:
            return await bot_client.send_message(chat_id, text, buttons=buttons, reply_to=reply_to)
        except:
            pass
    if userbot_client:
        try:
            return await userbot_client.send_message(chat_id, text, reply_to=reply_to)
        except:
            pass
    return None

async def reply_message(event, text, buttons=None):
    global bot_client, userbot_client
    chat_id = event.chat_id
    if await is_bot_in_group(chat_id):
        try:
            return await bot_client.send_message(chat_id, text, buttons=buttons, reply_to=event.id)
        except:
            pass
    try:
        return await event.reply(text)
    except:
        pass
    return None

async def delete_message_safe(chat_id, msg):
    global bot_client, userbot_client
    if not msg:
        return
    try:
        await msg.delete()
        return
    except:
        pass
    if bot_client:
        try:
            await bot_client.delete_messages(chat_id, msg.id)
            return
        except:
            pass
    if userbot_client:
        try:
            await userbot_client.delete_messages(chat_id, msg.id)
        except:
            pass

# ═══════════════════════════════════════════════════════════
#  BOT GRUP KONTROLÜ
# ═══════════════════════════════════════════════════════════
async def is_bot_in_group(chat_id):
    global bot_client, bot_in_group_cache
    if not bot_client:
        return False
    cache_key = f"bot_{chat_id}"
    now = time.time()
    if cache_key in bot_in_group_cache:
        cached_time, cached_result = bot_in_group_cache[cache_key]
        if now - cached_time < BOT_CACHE_DURATION:
            return cached_result
    try:
        bot_me = await bot_client.get_me()
        await bot_client(GetParticipantRequest(chat_id, bot_me.id))
        bot_in_group_cache[cache_key] = (now, True)
        return True
    except:
        bot_in_group_cache[cache_key] = (now, False)
        return False

# ═══════════════════════════════════════════════════════════
#  MÜZİK PANELİ  (renkli butonlar)
# ═══════════════════════════════════════════════════════════
def create_panel_buttons(chat_id):
    paused = is_paused.get(chat_id, False)
    elapsed = get_elapsed_time(chat_id)
    duration = 0
    is_live = False

    if chat_id in current_songs and current_songs[chat_id]:
        duration = current_songs[chat_id].get('duration', 0)
        is_live = current_songs[chat_id].get('is_live', False)

    if elapsed > duration and duration > 0:
        elapsed = duration

    # İlerleme çubuğu
    if is_live:
        progress_text = "🔴  CANLI YAYIN"
    else:
        bar = create_progress_bar(elapsed, duration)
        progress_text = f"⏱ {format_duration(elapsed)} {bar} {format_duration(duration)}"

    # Telethon'da inline button rengi desteklenmez, ama emoji + metin düzeni ile
    # "renkli" hissi verelim. Play/Pause butonunu duruma göre değiştiriyoruz.
    if paused:
        row1 = [Button.inline(f"▶️  Devam",      f"rs_{chat_id}"),
                Button.inline(f"⏹️  Bitir",       f"st_{chat_id}")]
    else:
        row1 = [Button.inline(f"⏸️  Duraklat",   f"ps_{chat_id}"),
                Button.inline(f"⏹️  Bitir",       f"st_{chat_id}")]

    row2 = [Button.inline(f"⏭️  Sonraki",     f"sk_{chat_id}"),
            Button.inline(f"📋  Kuyruk",       f"qu_{chat_id}")]

    row3 = [Button.inline(f"🔁  Tekrar Çal",  f"rp_{chat_id}"),
            Button.inline(f"🔀  Karıştır",    f"sh_{chat_id}")]

    progress_btn = [Button.inline(progress_text, f"np_{chat_id}")]

    return [progress_btn, row1, row2, row3]

def create_panel_text(chat_id):
    if chat_id not in current_songs or not current_songs[chat_id]:
        return "🔇 **Hiçbir şey çalmıyor.**"

    song = current_songs[chat_id]
    title = song.get('title', 'Bilinmeyen')
    paused = is_paused.get(chat_id, False)
    queue_count = len(music_queues.get(chat_id, []))
    requester = song.get('requester_name', 'Bilinmeyen')
    is_live = song.get('is_live', False)
    duration = song.get('duration', 0)

    status_icon = "⏸️" if paused else ("🔴" if is_live else "🎵")
    status_text = "Duraklatıldı" if paused else ("Canlı Yayın" if is_live else "Çalıyor")

    dur_text = ""
    if duration and not is_live:
        dur_text = f"\n⏳ **Süre:** `{format_duration(duration)}`"

    queue_text = f"  ·  📋 `{queue_count}` sırada" if queue_count > 0 else ""

    return (
        f"{status_icon} **{status_text}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎶 **{title}**\n"
        f"{dur_text}\n"
        f"👤 **İsteyen:** {requester}{queue_text}"
    )

# ═══════════════════════════════════════════════════════════
#  PANEL GÖNDER / GÜNCELLE / SİL
# ═══════════════════════════════════════════════════════════
async def delete_panel_message(chat_id):
    global bot_client, userbot_client
    if chat_id not in current_songs or not current_songs[chat_id]:
        return
    msg_id = current_songs[chat_id].get('message_id')
    panel_msg = current_songs[chat_id].get('panel_message')

    if panel_msg:
        try:
            await panel_msg.delete()
            return
        except:
            pass
    if bot_client and msg_id:
        try:
            await bot_client.delete_messages(chat_id, msg_id)
            return
        except:
            pass
    if userbot_client and msg_id:
        try:
            await userbot_client.delete_messages(chat_id, msg_id)
        except:
            pass

async def send_panel(chat_id):
    global userbot_client, bot_username, bot_client
    if not current_songs.get(chat_id):
        return None

    text    = create_panel_text(chat_id)
    buttons = create_panel_buttons(chat_id)

    if await is_bot_in_group(chat_id) and bot_client:
        try:
            msg = await bot_client.send_message(chat_id, text, buttons=buttons)
            if msg and current_songs.get(chat_id):
                current_songs[chat_id]['panel_message'] = msg
                current_songs[chat_id]['message_id']    = msg.id
                current_songs[chat_id]['sent_by_bot']   = True
            return msg
        except Exception as e:
            print(f"[PANEL] Bot gönderme hatası: {e}")

    # Fallback: inline query
    if userbot_client and bot_username:
        try:
            results = await userbot_client.inline_query(bot_username, f"panel_{chat_id}")
            if results:
                msg = await results[0].click(chat_id)
                if msg and current_songs.get(chat_id):
                    current_songs[chat_id]['panel_message'] = msg
                    current_songs[chat_id]['message_id']    = msg.id
                    current_songs[chat_id]['sent_by_bot']   = False
                return msg
        except Exception as e:
            print(f"[PANEL] Inline panel hatası: {e}")

    return None

async def update_panel_message(chat_id):
    global bot_client
    if chat_id not in current_songs or not current_songs[chat_id]:
        return False
    song = current_songs[chat_id]
    msg_id       = song.get('message_id')
    sent_by_bot  = song.get('sent_by_bot', False)
    if not msg_id or not sent_by_bot:
        return False

    text    = create_panel_text(chat_id)
    buttons = create_panel_buttons(chat_id)

    if bot_client:
        try:
            await bot_client.edit_message(chat_id, msg_id, text, buttons=buttons)
            return True
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" in str(e).upper():
                return True
    return False

async def panel_updater_task(chat_id):
    try:
        while is_playing.get(chat_id) and current_songs.get(chat_id):
            if not is_paused.get(chat_id, False):
                await update_panel_message(chat_id)
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[UPDATER] Hata: {e}")

def start_panel_updater(chat_id):
    if chat_id in panel_update_tasks:
        try:
            panel_update_tasks[chat_id].cancel()
        except:
            pass
    async def safe_updater():
        await asyncio.sleep(3)
        await panel_updater_task(chat_id)
    panel_update_tasks[chat_id] = asyncio.create_task(safe_updater())

def stop_panel_updater(chat_id):
    if chat_id in panel_update_tasks:
        try:
            panel_update_tasks[chat_id].cancel()
        except:
            pass
        del panel_update_tasks[chat_id]

# ═══════════════════════════════════════════════════════════
#  GRUP / KATILIM LOJİĞİ
# ═══════════════════════════════════════════════════════════
async def get_entity_safe(chat_id):
    for client in [music_client, userbot_client]:
        if client:
            try:
                return await client.get_entity(chat_id)
            except:
                pass
    return None

async def is_assistant_in_chat(chat_id):
    cache_key = f"in_chat_{chat_id}"
    now = time.time()
    if cache_key in assistant_status_cache:
        ct, cr = assistant_status_cache[cache_key]
        if now - ct < CACHE_DURATION:
            return cr
    try:
        me     = await music_client.get_me()
        entity = await get_entity_safe(chat_id)
        if not entity:
            assistant_status_cache[cache_key] = (now, False)
            return False
        await music_client(GetParticipantRequest(entity, me.id))
        assistant_status_cache[cache_key] = (now, True)
        return True
    except UserNotParticipantError:
        assistant_status_cache[cache_key] = (now, False)
        return False
    except:
        return False

async def check_chat_type(chat_id):
    result = {
        'is_private': False, 'is_supergroup': False,
        'has_join_request': False, 'can_join': True,
        'invite_link': None, 'entity': None,
        'username': None, 'error': None,
        'is_basic_group': False
    }
    try:
        entity = None
        if userbot_client:
            try:
                entity = await userbot_client.get_entity(chat_id)
            except:
                pass
        if not entity:
            entity = await get_entity_safe(chat_id)
        if not entity:
            result['error'] = 'entity_not_found'
            return result

        result['entity'] = entity

        if isinstance(entity, Channel):
            result['is_supergroup'] = entity.megagroup
            if hasattr(entity, 'username') and entity.username:
                result['is_private'] = False
                result['username']   = entity.username
            else:
                result['is_private'] = True
            try:
                if userbot_client:
                    full = await userbot_client(GetFullChannelRequest(entity))
                    if hasattr(full.full_chat, 'join_request'):
                        result['has_join_request'] = full.full_chat.join_request
                    if hasattr(full.full_chat, 'exported_invite') and full.full_chat.exported_invite:
                        result['invite_link'] = full.full_chat.exported_invite.link
            except:
                pass

        elif isinstance(entity, Chat):
            result['is_private']     = True
            result['is_basic_group'] = True
            result['is_supergroup']  = False

    except ChannelPrivateError:
        result['is_private'] = True
        result['can_join']   = False
        result['error']      = 'private_no_access'
    except Exception as e:
        result['error'] = str(e)

    return result

async def check_userbot_admin_rights(chat_id):
    try:
        me          = await userbot_client.get_me()
        participant = await userbot_client(GetParticipantRequest(chat_id, me.id))
        if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            if isinstance(participant.participant, ChannelParticipantCreator):
                return True, True
            rights     = participant.participant.admin_rights
            can_invite = getattr(rights, 'invite_users', False)
            return True, can_invite
        return False, False
    except:
        return False, False

async def try_join_chat(chat_id, chat_info=None):
    """
    Asistanı gruba eklemeye çalışır.
    Sıra: username → userbot davet → invite link → temel grup davet → manuel.
    """
    if chat_info is None:
        chat_info = await check_chat_type(chat_id)

    entity   = chat_info.get('entity')
    username = chat_info.get('username')

    if not entity:
        try:
            entity = await userbot_client.get_entity(chat_id)
            if hasattr(entity, 'username') and entity.username:
                username = entity.username
        except Exception as e:
            return False, f"❌ Grup bulunamadı: {e}"

    assistant_me = await music_client.get_me()

    try:
        # ── Süpergroup / Channel ────────────────────────────────
        if isinstance(entity, Channel):

            # 1) Public username ile join
            if username:
                try:
                    await music_client(JoinChannelRequest(username))
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Gruba katıldım!"
                except UserAlreadyParticipantError:
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Zaten gruptayım!"
                except FloodWaitError as e:
                    return False, f"⏳ Flood bekleme: {e.seconds} saniye"
                except UserBannedInChannelError:
                    return False, "❌ Bu gruptan yasaklanmışım!"
                except Exception as e:
                    if "join_request" in str(e).lower():
                        return False, "📝 Katılım isteği gönderildi, onay bekliyor."

            # 2) Userbot admin ise direkt davet et
            is_admin, can_invite = await check_userbot_admin_rights(chat_id)
            if can_invite:
                try:
                    await userbot_client(InviteToChannelRequest(entity, [assistant_me.id]))
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Davet edildi!"
                except UserAlreadyParticipantError:
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Zaten gruptayım!"
                except Exception as e:
                    if "mutual" in str(e).lower():
                        pass  # gizlilik engeli, invite link dene

            # 3) Invite link ile join (gizli gruplar için)
            if chat_info.get('invite_link'):
                try:
                    invite_hash = chat_info['invite_link'].split('/')[-1]
                    if invite_hash.startswith('+'):
                        invite_hash = invite_hash[1:]
                    await music_client(ImportChatInviteRequest(invite_hash))
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Davet linki ile katıldım!"
                except UserAlreadyParticipantError:
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Zaten gruptayım!"
                except InviteHashExpiredError:
                    return False, "❌ Davet linki süresi dolmuş, lütfen asistanı manuel ekleyin."
                except:
                    pass

            # 4) Invite link yoksa userbot'tan yeni link oluşturup dene
            if not chat_info.get('invite_link') and can_invite:
                try:
                    from telethon.tl.functions.messages import ExportChatInviteRequest
                    invite = await userbot_client(ExportChatInviteRequest(entity))
                    if invite and hasattr(invite, 'link'):
                        invite_hash = invite.link.split('/')[-1]
                        if invite_hash.startswith('+'):
                            invite_hash = invite_hash[1:]
                        await music_client(ImportChatInviteRequest(invite_hash))
                        assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                        return True, "✅ Yeni link ile katıldım!"
                except UserAlreadyParticipantError:
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Zaten gruptayım!"
                except:
                    pass

            return False, "❌ Otomatik eklenemedi — lütfen asistanı gruba manuel ekleyin."

        # ── Temel Grup (Chat) ───────────────────────────────────
        elif isinstance(entity, Chat):
            try:
                await userbot_client(AddChatUserRequest(chat_id, assistant_me.id, 100))
                assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                return True, "✅ Davet edildi!"
            except UserAlreadyParticipantError:
                assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                return True, "✅ Zaten gruptayım!"
            except ChatAdminRequiredError:
                return False, "❌ Temel grupta davet için admin yetkisi gerekli."
            except Exception as e:
                return False, f"❌ Hata: {e}"

    except Exception as e:
        return False, f"❌ Katılım hatası: {e}"

    return False, "❌ Bilinmeyen hata"

async def ensure_assistant_in_chat(chat_id):
    if await is_assistant_in_chat(chat_id):
        return True, None
    chat_info = await check_chat_type(chat_id)
    return await try_join_chat(chat_id, chat_info)

# ═══════════════════════════════════════════════════════════
#  SESLİ SOHBETE KATILIM
# ═══════════════════════════════════════════════════════════
async def try_join_voice_chat(chat_id, stream):
    """py-tgcalls 2.x: play() hem join hem değiştirme görevi görüyor."""
    # Telethon entity cache'ini önceden doldur
    try:
        if music_client and music_client.is_connected():
            try:
                await music_client.get_entity(chat_id)
            except Exception:
                if userbot_client:
                    try:
                        entity = await userbot_client.get_entity(chat_id)
                        if hasattr(entity, 'username') and entity.username:
                            await music_client.get_entity(entity.username)
                    except:
                        pass
    except:
        pass

    try:
        await pytgcalls_client.play(chat_id, stream)
        return True, None
    except Exception as e:
        error_str  = str(e).lower()
        error_name = type(e).__name__

        # Entity bulunamadı → gruba katılmayı dene, tekrar play
        if "could not find" in error_str or "input entity" in error_str or "peerchannel" in error_str:
            try:
                entity = await userbot_client.get_entity(chat_id)
                if hasattr(entity, 'username') and entity.username:
                    await music_client(JoinChannelRequest(entity.username))
            except:
                pass
            try:
                await pytgcalls_client.play(chat_id, stream)
                return True, None
            except Exception as e2:
                return False, f"❌ Entity hatası — müzik hesabını gruba ekleyin: {e2}"

        if "noactivegroupcall" in error_name.lower() or "no active" in error_str:
            return False, "no_active_call"
        if "groupcallnotfound" in error_name.lower():
            return False, "no_active_call"
        if "not a member" in error_str or "participant" in error_str:
            return False, "need_join"

        return False, f"❌ Sesli sohbet hatası: {e}"

# ═══════════════════════════════════════════════════════════
#  TEMİZLİK
# ═══════════════════════════════════════════════════════════
async def cleanup_music(chat_id, message=None, send_notification=True):
    stop_panel_updater(chat_id)
    await delete_panel_message(chat_id)

    for d in [music_queues, download_status]:
        if chat_id in d:
            del d[chat_id]

    if chat_id in download_tasks:
        for task in download_tasks[chat_id].values():
            try:
                task.cancel()
            except:
                pass
        del download_tasks[chat_id]

    is_playing[chat_id]  = False
    is_paused[chat_id]   = False
    current_songs[chat_id] = None

    if send_notification and message:
        await send_message(chat_id, f"📭 {message}")

# ═══════════════════════════════════════════════════════════
#  İNDİRME
# ═══════════════════════════════════════════════════════════
class DownloadStatus:
    WAITING     = "waiting"
    DOWNLOADING = "downloading"
    PROCESSING  = "processing"
    READY       = "ready"
    ERROR       = "error"

DOWNLOAD_EMOJI = {
    DownloadStatus.WAITING:     "⏳",
    DownloadStatus.DOWNLOADING: "⬇️",
    DownloadStatus.PROCESSING:  "🔄",
    DownloadStatus.READY:       "✅",
    DownloadStatus.ERROR:       "❌",
}

def update_download_status(chat_id, queue_index, status, progress=None):
    if chat_id not in download_status:
        download_status[chat_id] = {}
    download_status[chat_id][queue_index] = {
        'status': status, 'progress': progress, 'updated_at': time.time()
    }

def get_queue_with_status(chat_id):
    if chat_id not in music_queues:
        return []
    result = []
    for i, item in enumerate(music_queues[chat_id]):
        status_info = download_status.get(chat_id, {}).get(i, {})
        status = status_info.get('status', DownloadStatus.WAITING)
        if item.get('path') and os.path.exists(item['path']):
            status = DownloadStatus.READY
        result.append({**item, 'download_status': status,
                        'status_emoji': DOWNLOAD_EMOJI.get(status, "❓")})
    return result

async def download_item(chat_id, item, queue_index):
    try:
        update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING)
        path     = ""
        video_id = ""
        title    = item.get('title', 'Bilinmeyen')
        duration = item.get('duration', 0)

        # ── Telegram ses dosyası ──────────────────────────────
        if item['type'] == 'tg':
            msg      = item['data']
            video_id = f"tg_{msg.id}"
            path     = f"/tmp/{video_id}.mp3"
            if not os.path.exists(path):
                update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING, 50)
                await msg.download_media(file=path)
            for src in [msg.audio, msg.voice]:
                if src and hasattr(src, 'duration'):
                    duration = src.duration or duration
                    break
            if msg.document:
                for attr in msg.document.attributes:
                    if hasattr(attr, 'duration'):
                        duration = attr.duration
                        break
            if msg.file and hasattr(msg.file, 'title') and msg.file.title:
                title = msg.file.title
            elif msg.audio and hasattr(msg.audio, 'title') and msg.audio.title:
                title = msg.audio.title
            else:
                title = "Ses Dosyası"

        # ── YouTube / URL ─────────────────────────────────────
        elif item['type'] == 'yt':
            query     = item['data']
            is_live   = False
            stream_url = None

            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    search = query if "http" in query else f"ytsearch:{query}"
                    info   = await asyncio.to_thread(ydl.extract_info, search, download=False)
                    if not info:
                        raise Exception("Video bulunamadı")
                    if 'entries' in info:
                        if not info['entries']:
                            raise Exception("Sonuç yok")
                        info = info['entries'][0]
                    if not info.get('id'):
                        raise Exception("Video ID alınamadı")

                    video_id = info['id']
                    title    = info.get('title', 'YouTube')
                    duration = info.get('duration', 0) or 0
                    url      = f"https://www.youtube.com/watch?v={video_id}"
                    is_live  = info.get('is_live', False) or info.get('live_status') == 'is_live'

                    if is_live:
                        fmts = info.get('formats', [])
                        audio_fmts = [f for f in fmts if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                        stream_url = (audio_fmts[-1].get('url') if audio_fmts
                                      else info.get('url') or (fmts[-1].get('url') if fmts else None))
                        if not stream_url:
                            raise Exception("Canlı yayın URL'i alınamadı")
                        item.update({'is_live': True, 'stream_url': stream_url,
                                     'title': f"🔴 {title}", 'duration': 0,
                                     'path': stream_url})
                        update_download_status(chat_id, queue_index, DownloadStatus.READY)
                        return True

            except Exception as e:
                print(f"YouTube hatası: {e}")
                update_download_status(chat_id, queue_index, DownloadStatus.ERROR)
                return False

            path     = f"/tmp/{video_id}.mp3"
            log_msg  = await get_audio_from_log(video_id)

            if log_msg:
                update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING, 75)
                await log_msg.download_media(file=path)
                try:
                    if log_msg.audio:
                        duration = log_msg.audio.duration or duration
                    elif log_msg.document:
                        for attr in log_msg.document.attributes:
                            if hasattr(attr, 'duration'):
                                duration = attr.duration
                                break
                except:
                    pass
            else:
                update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING, 25)
                with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                    await asyncio.to_thread(ydl.download, [url])
                update_download_status(chat_id, queue_index, DownloadStatus.PROCESSING)
                if os.path.exists(path):
                    try:
                        attr = [DocumentAttributeAudio(duration=int(duration), title=title)]
                        await music_client.send_file(
                            LOG_GROUP, path,
                            caption=f"🎵 {title}\n🆔 `{video_id}`",
                            attributes=attr
                        )
                    except:
                        pass

        if os.path.exists(path):
            item.update({'path': path, 'title': title, 'duration': duration})
            update_download_status(chat_id, queue_index, DownloadStatus.READY)
            return True

        update_download_status(chat_id, queue_index, DownloadStatus.ERROR)
        return False

    except Exception as e:
        update_download_status(chat_id, queue_index, DownloadStatus.ERROR)
        print(f"İndirme hatası: {e}")
        return False

async def preload_queue(chat_id, start_index=0, count=2):
    if chat_id not in music_queues:
        return
    for i in range(start_index, min(start_index + count, len(music_queues[chat_id]))):
        item = music_queues[chat_id][i]
        if item.get('path') and os.path.exists(item['path']):
            update_download_status(chat_id, i, DownloadStatus.READY)
            continue
        if chat_id not in download_tasks:
            download_tasks[chat_id] = {}
        if i not in download_tasks[chat_id]:
            download_tasks[chat_id][i] = asyncio.create_task(
                download_item(chat_id, item, i)
            )

# ═══════════════════════════════════════════════════════════
#  OYNATMA
# ═══════════════════════════════════════════════════════════
async def play_logic(chat_id, item):
    path       = item.get('path')
    title      = item.get('title', 'Bilinmeyen')
    duration   = item.get('duration', 0)
    is_live    = item.get('is_live', False)
    stream_url = item.get('stream_url')

    if not is_live and (not path or not os.path.exists(path)):
        success = await download_item(chat_id, item, -1)
        if not success:
            return False, "❌ İndirme başarısız", 0
        path       = item.get('path')
        title      = item.get('title', title)
        duration   = item.get('duration', duration)
        is_live    = item.get('is_live', False)
        stream_url = item.get('stream_url')

    if is_live:
        if not stream_url:
            return False, "❌ Canlı yayın URL'i bulunamadı", 0
    else:
        if not path or not os.path.exists(path):
            return False, "❌ Dosya bulunamadı", 0

    try:
        stream = MediaStream(stream_url if is_live else path)

        # Önce asistanın grupta olup olmadığını kontrol et
        assistant_in_chat = await is_assistant_in_chat(chat_id)
        if not assistant_in_chat:
            join_success, join_msg = await ensure_assistant_in_chat(chat_id)
            if not join_success:
                return False, join_msg, 0
            await asyncio.sleep(0.5)

        success, error_msg = await try_join_voice_chat(chat_id, stream)

        if not success:
            if error_msg in ("no_active_call", "need_join"):
                # Aktif sesli sohbet yok — kullanıcıya açık mesaj
                if error_msg == "no_active_call":
                    return False, "❌ Aktif sesli sohbet yok! Önce bir sesli sohbet başlatın.", 0
                return False, error_msg or "❌ Sesli sohbete katılamadım", 0
            return False, error_msg, 0

        is_playing[chat_id]  = True
        is_paused[chat_id]   = False

        current_songs[chat_id] = {
            'title':          title,
            'duration':       duration,
            'started_at':     time.time(),
            'message_id':     None,
            'chat_id':        chat_id,
            'is_live':        is_live,
            'requester_name': item.get('requester_name', 'Bilinmeyen'),
            'requester_id':   item.get('requester_id'),
        }

        msg = await send_panel(chat_id)
        if msg:
            current_songs[chat_id]['message_id'] = msg.id

        if not is_live:
            start_panel_updater(chat_id)

        asyncio.create_task(preload_queue(chat_id, 0, 2))
        return True, title, duration

    except Exception as e:
        return False, str(e), 0

async def next_song(chat_id):
    stop_panel_updater(chat_id)
    await delete_panel_message(chat_id)

    if chat_id in music_queues and music_queues[chat_id]:
        next_item = music_queues[chat_id].pop(0)

        # İndirme durumu sıralamasını güncelle
        if chat_id in download_status:
            download_status[chat_id] = {
                i - 1: v for i, v in download_status[chat_id].items() if i > 0
            }

        notify = await send_message(
            chat_id, f"⏭️ **Sıradaki:** `{next_item.get('title', 'Yükleniyor...')}`"
        )
        await asyncio.sleep(1)
        if notify:
            await delete_message_safe(chat_id, notify)

        success, title, duration = await play_logic(chat_id, next_item)
        if not success:
            await next_song(chat_id)
    else:
        await send_message(chat_id, "📭 **Kuyruk bitti, sesli sohbetten ayrılıyorum.**")
        try:
            await pytgcalls_client.leave_call(chat_id)
        except:
            pass
        is_playing[chat_id]    = False
        is_paused[chat_id]     = False
        current_songs[chat_id] = None
        music_queues.pop(chat_id, None)

# ═══════════════════════════════════════════════════════════
#  BAĞLANTI / INIT
# ═══════════════════════════════════════════════════════════
async def init_music(api_id, api_hash):
    global music_client, pytgcalls_client, handlers_registered

    if music_client is None:
        music_client = TelegramClient(StringSession(MUSIC_SESSION), api_id, api_hash)

    if not music_client.is_connected():
        try:
            await music_client.start()
        except Exception as e:
            print(f"[MUSIC] Bağlantı hatası: {e}")
            return False

    if pytgcalls_client is None:
        pytgcalls_client = PyTgCalls(music_client)

    if not handlers_registered:
        import pytgcalls.filters as _f
        from pytgcalls.types import ChatUpdate

        @pytgcalls_client.on_update(_f.stream_end)
        async def _on_stream_end(client, update):
            await next_song(update.chat_id)

        @pytgcalls_client.on_update(_f.chat_update)
        async def _on_chat_update(client, update):
            cid    = update.chat_id
            status = getattr(update, 'status', None)
            msgs   = {
                ChatUpdate.Status.LEFT_GROUP:        "Sesli sohbet sonlandı.",
                ChatUpdate.Status.KICKED:            "Sesli sohbetten atıldım!",
                ChatUpdate.Status.CLOSED_VOICE_CHAT: "Sesli sohbet kapatıldı.",
            }
            if status in msgs:
                if is_playing.get(cid) and current_songs.get(cid):
                    await cleanup_music(cid, msgs[status], True)
                else:
                    await cleanup_music(cid, None, False)

        handlers_registered = True
        try:
            await pytgcalls_client.start()
        except:
            pass

    return True

# ═══════════════════════════════════════════════════════════
#  USERBOT KOMUTLARI
# ═══════════════════════════════════════════════════════════
def register(client):
    global userbot_client, OWNER_ID
    userbot_client = client

    async def _set_owner():
        global OWNER_ID
        me = await client.get_me()
        OWNER_ID = me.id
    client.loop.create_task(_set_owner())

    # ── .cal ────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.cal(?:\s+(.+))?$'))
    async def play_handler(event):
        chat_id        = event.chat_id
        sender         = await event.get_sender()
        requester_name = sender.first_name if sender else "Bilinmeyen"
        requester_id   = event.sender_id

        if not check_permission(event.sender_id, chat_id):
            return

        if not await init_music(client.api_id, client.api_hash):
            return await reply_message(event, "❌ Müzik bağlantısı kurulamadı.")

        query = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        item  = {}
        display_title = ""

        if reply and (reply.audio or reply.voice or
                      (reply.document and reply.document.mime_type
                       and 'audio' in reply.document.mime_type)):
            duration = 0
            for src in [reply.audio, reply.voice]:
                if src and hasattr(src, 'duration'):
                    duration = src.duration or 0
                    break
            if reply.document:
                for attr in reply.document.attributes:
                    if hasattr(attr, 'duration'):
                        duration = attr.duration or 0
                        break
            title = "Ses Dosyası"
            if reply.file and hasattr(reply.file, 'title') and reply.file.title:
                title = reply.file.title
            elif reply.audio and hasattr(reply.audio, 'title') and reply.audio.title:
                title = reply.audio.title
            item = {'type': 'tg', 'data': reply, 'title': title,
                    'duration': duration, 'requester_name': requester_name,
                    'requester_id': requester_id}
            display_title = title

        elif query:
            item = {'type': 'yt', 'data': query, 'title': query,
                    'duration': 0, 'requester_name': requester_name,
                    'requester_id': requester_id}
            display_title = query
        else:
            return await reply_message(event, "❌ Şarkı adı yaz veya ses dosyasına yanıt ver!")

        # Kuyruk
        if is_playing.get(chat_id):
            if chat_id not in music_queues:
                music_queues[chat_id] = []
            q_idx = len(music_queues[chat_id])
            music_queues[chat_id].append(item)
            update_download_status(chat_id, q_idx, DownloadStatus.WAITING)
            msg = await reply_message(
                event,
                f"➕ **Kuyruğa Eklendi**\n"
                f"🎵 `{display_title}`\n"
                f"👤 {requester_name} · 📋 Sıra: {q_idx + 1}"
            )
            async def _dl_notify():
                ok = await download_item(chat_id, item, q_idx)
                try:
                    if msg:
                        if ok:
                            await msg.edit(
                                f"✅ **Hazır**\n🎵 `{item.get('title', display_title)}`\n"
                                f"👤 {requester_name} · ⏱ {format_duration(item.get('duration', 0))}"
                            )
                        else:
                            await msg.edit(f"❌ **İndirme başarısız:** `{display_title}`")
                except:
                    pass
            asyncio.create_task(_dl_notify())
            return

        m = await reply_message(event, f"⚡ **Hazırlanıyor:** `{display_title}`")
        success, res, dur = await play_logic(chat_id, item)
        if success:
            await delete_message_safe(chat_id, m)
        else:
            try:
                await m.edit(f"{res}")
            except:
                pass

    # ── .atla ───────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.atla$'))
    async def skip_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        if not is_playing.get(event.chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        sender = await event.get_sender()
        name   = sender.first_name if sender else "Bilinmeyen"
        await reply_message(event, f"⏭️ **{name}** sonraki şarkıya geçti.")
        await next_song(event.chat_id)

    # ── .bitir ──────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.bitir$'))
    async def stop_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        if not is_playing.get(chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        sender = await event.get_sender()
        name   = sender.first_name if sender else "Bilinmeyen"
        await cleanup_music(chat_id, None, False)
        try:
            await pytgcalls_client.leave_call(chat_id)
        except:
            pass
        await reply_message(event, f"⏹️ **{name}** müziği durdurdu.")

    # ── .durdur ─────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.durdur$'))
    async def pause_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        if not is_playing.get(chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        if is_paused.get(chat_id):
            return await reply_message(event, "⏸️ Zaten duraklatılmış.")
        try:
            await pytgcalls_client.pause(chat_id)
            is_paused[chat_id] = True
            if current_songs.get(chat_id):
                current_songs[chat_id]['paused_at'] = time.time()
            await update_panel_message(chat_id)
            await reply_message(event, "⏸️ **Duraklatıldı.**")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    # ── .devam ──────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.devam$'))
    async def resume_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        if not is_playing.get(chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        if not is_paused.get(chat_id):
            return await reply_message(event, "▶️ Zaten çalıyor.")
        try:
            await pytgcalls_client.resume(chat_id)
            if current_songs.get(chat_id):
                paused_at  = current_songs[chat_id].get('paused_at', time.time())
                started_at = current_songs[chat_id].get('started_at', time.time())
                current_songs[chat_id]['started_at'] = started_at + (time.time() - paused_at)
            is_paused[chat_id] = False
            await update_panel_message(chat_id)
            await reply_message(event, "▶️ **Devam ediliyor.**")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    # ── .kuyruk ─────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.kuyruk$'))
    async def queue_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        items   = get_queue_with_status(chat_id)
        if items:
            total_dur = sum(s.get('duration', 0) for s in items)
            lines = [f"📋 **Sıradaki Şarkılar** ({len(items)})\n"]
            for i, s in enumerate(items[:15], 1):
                dur  = format_duration(s.get('duration', 0))
                icon = s.get('status_emoji', '⏳')
                req  = s.get('requester_name', '')
                line = f"{icon} **{i}.** {s['title'][:35]}"
                if s.get('duration'):
                    line += f"  `[{dur}]`"
                if req:
                    line += f"  — {req}"
                lines.append(line)
            if len(items) > 15:
                lines.append(f"\n_...ve {len(items) - 15} şarkı daha_")
            lines.append(f"\n⏱ **Toplam süre:** `{format_duration(total_dur)}`")
            await reply_message(event, "\n".join(lines))
        else:
            await reply_message(event, "📭 **Kuyruk boş.**")

    # ── .np ─────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.np$'))
    async def nowplaying_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        if current_songs.get(chat_id):
            await delete_panel_message(chat_id)
            msg = await send_panel(chat_id)
            if msg and current_songs.get(chat_id):
                current_songs[chat_id]['message_id']    = msg.id
                current_songs[chat_id]['panel_message'] = msg
        else:
            await reply_message(event, "🔇 **Şu an çalan yok.**")

    # ── .ses ────────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.ses(?:\s+(\d+))?$'))
    async def volume_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        chat_id = event.chat_id
        if not is_playing.get(chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        arg = event.pattern_match.group(1)
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.ses 50` (0-200 arası)")
        vol = int(arg)
        if not 0 <= vol <= 200:
            return await reply_message(event, "❌ Ses seviyesi 0-200 arasında olmalı.")
        try:
            await pytgcalls_client.change_volume_call(chat_id, vol)
            await reply_message(event, f"🔊 **Ses seviyesi:** {vol}%")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    # ── Özel mod ────────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.ozmod$'))
    async def private_on_handler(event):
        if event.sender_id != OWNER_ID:
            return
        private_mode[event.chat_id] = True
        await reply_message(event, "🔒 **Özel mod AÇIK** — Sadece yetkili kullanıcılar kullanabilir.")

    @client.on(events.NewMessage(pattern=r'^\.ozmodkapat$'))
    async def private_off_handler(event):
        if event.sender_id != OWNER_ID:
            return
        private_mode[event.chat_id] = False
        await reply_message(event, "🔓 **Özel mod KAPALI** — Herkes kullanabilir.")

    # ── Yetki komutları ─────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.izinver(?:\s+(.+))?$'))
    async def allow_handler(event):
        if event.sender_id != OWNER_ID:
            return
        arg   = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if reply:
            if add_allowed_user(reply.sender_id):
                return await reply_message(event, f"✅ `{reply.sender_id}` izin listesine eklendi.")
            return await reply_message(event, "ℹ️ Zaten izinli.")
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.izinver @kullanıcı` veya yanıt ver")
        try:
            target_id = (await client.get_entity(arg)).id if arg.startswith('@') else int(arg)
            fn = add_allowed_group if target_id < 0 else add_allowed_user
            label = "Grup" if target_id < 0 else "Kullanıcı"
            if fn(target_id):
                await reply_message(event, f"✅ {label} `{target_id}` izin listesine eklendi.")
            else:
                await reply_message(event, f"ℹ️ {label} zaten izinli.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.izinkaldir(?:\s+(.+))?$'))
    async def disallow_handler(event):
        if event.sender_id != OWNER_ID:
            return
        arg   = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if reply:
            if remove_allowed_user(reply.sender_id):
                return await reply_message(event, f"✅ `{reply.sender_id}` izin listesinden çıkarıldı.")
            return await reply_message(event, "ℹ️ Zaten izinli değil.")
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.izinkaldir @kullanıcı`")
        try:
            target_id = (await client.get_entity(arg)).id if arg.startswith('@') else int(arg)
            fn = remove_allowed_group if target_id < 0 else remove_allowed_user
            label = "Grup" if target_id < 0 else "Kullanıcı"
            if fn(target_id):
                await reply_message(event, f"✅ {label} `{target_id}` izin listesinden çıkarıldı.")
            else:
                await reply_message(event, f"ℹ️ {label} zaten izinli değil.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.engelle(?:\s+(.+))?$'))
    async def block_handler(event):
        if event.sender_id != OWNER_ID:
            return
        chat_id = event.chat_id
        reply   = await event.get_reply_message()
        arg     = event.pattern_match.group(1)
        if reply:
            uid = reply.sender_id
            msg = "engellendi" if block_user_in_group(uid, chat_id) else "zaten engelli"
            return await reply_message(event, f"🚫 `{uid}` bu grupta {msg}.")
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.engelle @kullanıcı` veya yanıt ver")
        try:
            uid = (await client.get_entity(arg)).id if arg.startswith('@') else int(arg)
            msg = "engellendi" if block_user_in_group(uid, chat_id) else "zaten engelli"
            await reply_message(event, f"🚫 `{uid}` bu grupta {msg}.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.engelkaldir(?:\s+(.+))?$'))
    async def unblock_handler(event):
        if event.sender_id != OWNER_ID:
            return
        chat_id = event.chat_id
        reply   = await event.get_reply_message()
        arg     = event.pattern_match.group(1)
        if reply:
            uid = reply.sender_id
            msg = "engel kaldırıldı" if unblock_user_in_group(uid, chat_id) else "zaten engelli değil"
            return await reply_message(event, f"✅ `{uid}` — {msg}.")
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.engelkaldir @kullanıcı`")
        try:
            uid = (await client.get_entity(arg)).id if arg.startswith('@') else int(arg)
            msg = "engel kaldırıldı" if unblock_user_in_group(uid, chat_id) else "zaten engelli değil"
            await reply_message(event, f"✅ `{uid}` — {msg}.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.izinliste$'))
    async def permissions_list_handler(event):
        if event.sender_id != OWNER_ID:
            return
        lines = ["📋 **İzin Listesi**\n"]
        lines.append("👤 **İzinli Kullanıcılar:**")
        for uid in permissions_data["allowed_users"] or ["—"]:
            lines.append(f"  • `{uid}`")
        lines.append("\n👥 **İzinli Gruplar:**")
        for gid in permissions_data["allowed_groups"] or ["—"]:
            lines.append(f"  • `{gid}`")
        lines.append("\n🚫 **Engelli Kullanıcılar:**")
        for gid, users in permissions_data["blocked_users"].items():
            if users:
                lines.append(f"  Grup `{gid}`:")
                for uid in users:
                    lines.append(f"    • `{uid}`")
        if not any(permissions_data["blocked_users"].values()):
            lines.append("  —")
        await reply_message(event, "\n".join(lines))

    # ── .muzikhelp ──────────────────────────────────────────
    @client.on(events.NewMessage(pattern=r'^\.muzikhelp$'))
    async def help_handler(event):
        await reply_message(event, (
            "🎵 **MÜZİK KOMUTLARI**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**▶️ Temel**\n"
            "`.cal <şarkı/URL>` — Çal veya kuyruğa ekle\n"
            "`.atla` — Sonraki şarkı\n"
            "`.bitir` — Durdur ve çık\n"
            "`.durdur` — Duraklat\n"
            "`.devam` — Devam et\n"
            "`.ses <0-200>` — Ses seviyesi\n\n"
            "**ℹ️ Bilgi**\n"
            "`.kuyruk` — Kuyruk listesi\n"
            "`.np` — Şu an çalan (panel yenile)\n\n"
            "**🔒 Özel Mod (Sahip)**\n"
            "`.ozmod` — Özel mod aç\n"
            "`.ozmodkapat` — Özel mod kapat\n\n"
            "**⚙️ Yetki (Sahip)**\n"
            "`.izinver @k/id` — İzin ver\n"
            "`.izinkaldir @k/id` — İzin kaldır\n"
            "`.engelle @k` — Grupta engelle\n"
            "`.engelkaldir @k` — Engel kaldır\n"
            "`.izinliste` — İzin listesi"
        ))

# ═══════════════════════════════════════════════════════════
#  BOT KOMUTLARI  (callback + inline)
# ═══════════════════════════════════════════════════════════
def register_bot(bot, client):
    global bot_username, bot_client
    bot_client = bot

    async def _set_name():
        global bot_username
        me = await bot.get_me()
        bot_username = me.username
    bot.loop.create_task(_set_name())

    # ── Inline panel ────────────────────────────────────────
    @bot.on(events.InlineQuery(pattern=r'^panel_(-?\d+)$'))
    async def panel_inline_handler(event):
        chat_id = int(event.pattern_match.group(1))
        if not current_songs.get(chat_id) or not is_playing.get(chat_id):
            return
        await event.answer([
            event.builder.article(
                title="🎵 Müzik Paneli",
                description=f"Çalıyor: {current_songs[chat_id].get('title', 'Bilinmeyen')}",
                text=create_panel_text(chat_id),
                buttons=create_panel_buttons(chat_id)
            )
        ], cache_time=0)

    # ── Callback ────────────────────────────────────────────
    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        data = event.data.decode()
        try:
            parts   = data.split("_")
            action  = parts[0]
            chat_id = int(parts[1])

            # ⏸ Duraklat
            if action == "ps":
                if is_playing.get(chat_id) and not is_paused.get(chat_id):
                    try:
                        await pytgcalls_client.pause(chat_id)
                        is_paused[chat_id] = True
                        if current_songs.get(chat_id):
                            current_songs[chat_id]['paused_at'] = time.time()
                        await event.edit(create_panel_text(chat_id),
                                         buttons=create_panel_buttons(chat_id))
                        await event.answer("⏸️ Duraklatıldı", alert=False)
                    except Exception as e:
                        await event.answer(f"Hata: {e}", alert=True)
                else:
                    await event.answer("Zaten duraklatılmış", alert=False)

            # ▶ Devam
            elif action == "rs":
                if is_playing.get(chat_id) and is_paused.get(chat_id):
                    try:
                        await pytgcalls_client.resume(chat_id)
                        if current_songs.get(chat_id):
                            paused_at  = current_songs[chat_id].get('paused_at', time.time())
                            started_at = current_songs[chat_id].get('started_at', time.time())
                            current_songs[chat_id]['started_at'] = started_at + (time.time() - paused_at)
                        is_paused[chat_id] = False
                        await event.edit(create_panel_text(chat_id),
                                         buttons=create_panel_buttons(chat_id))
                        await event.answer("▶️ Devam", alert=False)
                    except Exception as e:
                        await event.answer(f"Hata: {e}", alert=True)
                else:
                    await event.answer("Zaten çalıyor", alert=False)

            # ⏭ Sonraki
            elif action == "sk":
                try:
                    user = await event.get_sender()
                    name = user.first_name if user else "Birisi"
                except:
                    name = "Birisi"
                await event.answer("⏭️ Atlanıyor...", alert=False)
                await send_message(chat_id, f"⏭️ **{name}** sonraki şarkıya geçti.")
                await next_song(chat_id)

            # ⏹ Bitir
            elif action == "st":
                try:
                    user = await event.get_sender()
                    name = user.first_name if user else "Birisi"
                except:
                    name = "Birisi"
                try:
                    await event.delete()
                except:
                    pass
                await cleanup_music(chat_id, None, False)
                try:
                    await pytgcalls_client.leave_call(chat_id)
                except:
                    pass
                await event.answer("⏹️ Durduruldu", alert=False)
                await send_message(chat_id, f"⏹️ **{name}** müziği durdurdu.")

            # 🔁 Tekrar çal
            elif action == "rp":
                if current_songs.get(chat_id):
                    song = current_songs[chat_id]
                    # Aynı şarkıyı kuyruğun başına ekle
                    replay_item = {
                        'type':           'yt' if not song.get('is_tg') else 'tg',
                        'data':           song.get('data') or song.get('title', ''),
                        'title':          song.get('title', ''),
                        'duration':       song.get('duration', 0),
                        'path':           song.get('path', ''),
                        'requester_name': song.get('requester_name', ''),
                        'requester_id':   song.get('requester_id'),
                    }
                    if chat_id not in music_queues:
                        music_queues[chat_id] = []
                    music_queues[chat_id].insert(0, replay_item)
                    await event.answer("🔁 Şarkı tekrar kuyruğa eklendi", alert=False)
                else:
                    await event.answer("Çalan şarkı yok", alert=False)

            # 🔀 Karıştır
            elif action == "sh":
                if chat_id in music_queues and len(music_queues[chat_id]) > 1:
                    import random
                    random.shuffle(music_queues[chat_id])
                    await event.answer("🔀 Kuyruk karıştırıldı!", alert=False)
                else:
                    await event.answer("Karıştırmak için en az 2 şarkı gerekli", alert=False)

            # 📋 Kuyruk (popup)
            elif action == "qu":
                items = get_queue_with_status(chat_id)
                if items:
                    lines = "\n".join(
                        f"{s['status_emoji']} {i}. {s['title'][:28]}"
                        for i, s in enumerate(items[:8], 1)
                    )
                    extra = f"\n...+{len(items) - 8}" if len(items) > 8 else ""
                    await event.answer(f"📋 Kuyruk ({len(items)}):\n{lines}{extra}", alert=True)
                else:
                    await event.answer("📭 Kuyruk boş", alert=True)

            # İlerleme çubuğuna tıklama
            elif action == "np":
                if current_songs.get(chat_id):
                    elapsed  = get_elapsed_time(chat_id)
                    duration = current_songs[chat_id].get('duration', 0)
                    await event.answer(
                        f"⏱ {format_duration(elapsed)} / {format_duration(duration)}",
                        alert=False
                    )
                else:
                    await event.answer("🎵 Çalıyor...", alert=False)

        except Exception as e:
            await event.answer("Bir hata oluştu", alert=False)
            print(f"[CALLBACK] Hata: {e}")
