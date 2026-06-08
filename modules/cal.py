import asyncio
import os
import logging
import time
import json
from telethon import events, Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeAudio
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest, GetFullChannelRequest, InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetFullChatRequest, AddChatUserRequest
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
    # Eski import'lar kaldırıldı (py-tgcalls >= 1.0.0 ile uyumsuz)
    # AudioPiped -> MediaStream, InputAudioStream/HighQualityAudio -> yok
    try:
        from pytgcalls.exceptions import (
            NoActiveGroupCall, GroupCallNotFound,
            AlreadyJoinedError, NotInGroupCallError
        )
    except ImportError:
        # Yeni sürümlerde exception isimleri değişti
        class NoActiveGroupCall(Exception): pass
        class GroupCallNotFound(Exception): pass
        class AlreadyJoinedError(Exception): pass
        class NotInGroupCallError(Exception): pass
except:
    pass

# ================= AYARLAR =================
DEFAULT_MUSIC_SESSION = "1BJWap1sBuzlsIh9jRJzHeFGHx7GiC-Por9cwTk8MisHFv6gxoUQXc5zGQz-KMTKyD6owZs_9FUoTMRYBd38hkZl8jQq4shETjkzVWZs2eUBgBjcpCv--pWztp8BNwC5UFpPWGva1U-6azdsyEHloPzhuJPvokYs10js--knr6GaeUV0nEOJ5cbBeqbi4l0Pfkqgxo_XjobMv9WenrsR7r1_l2Y0kOC_q6zSJZqcMmk8mbctqMqGCkqFTaTebOTVpIffVQHNNyumtriUzGN6rS4tCJXeYbN2zdY8i7PmfpmipfAdk8CseX-sUKZKS03EUh3F2ntgytzzqptbP1OPpZ3xDqe7lUEE="
MUSIC_SESSION = os.getenv("MUSIC_SESSION", DEFAULT_MUSIC_SESSION)
LOG_GROUP = -5027859960
OWNER_ID = None
PERMISSIONS_FILE = "music_permissions.json"

# ================= GLOBAL DEĞİŞKENLER =================
music_client = None
pytgcalls = None
userbot_client = None
bot_client = None
bot_username = None
handlers_registered = False

# Müzik durumu
music_queues = {}
current_songs = {}
is_playing = {}
is_paused = {}
private_mode = {}

# İndirme durumu
download_status = {}
download_tasks = {}

# Panel güncelleme
panel_update_tasks = {}

# Bot grup cache
bot_in_group_cache = {}
BOT_CACHE_DURATION = 600

# Cache
assistant_status_cache = {}
CACHE_DURATION = 300

# ================= YETKİ SİSTEMİ =================
# {
#   "allowed_users": [user_id, ...],
#   "allowed_groups": [group_id, ...],
#   "blocked_users": {"group_id": [user_id, ...], ...}
# }
permissions_data = {
    "allowed_users": [],
    "allowed_groups": [],
    "blocked_users": {}
}

def load_permissions():
    """Yetkileri dosyadan yükle"""
    global permissions_data
    try:
        if os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, 'r') as f:
                permissions_data = json.load(f)
    except:
        pass

def save_permissions():
    """Yetkileri dosyaya kaydet"""
    try:
        with open(PERMISSIONS_FILE, 'w') as f:
            json.dump(permissions_data, f, indent=2)
    except:
        pass

def add_allowed_user(user_id):
    """Kullanıcıya izin ver"""
    if user_id not in permissions_data["allowed_users"]:
        permissions_data["allowed_users"].append(user_id)
        save_permissions()
        return True
    return False

def remove_allowed_user(user_id):
    """Kullanıcı iznini kaldır"""
    if user_id in permissions_data["allowed_users"]:
        permissions_data["allowed_users"].remove(user_id)
        save_permissions()
        return True
    return False

def add_allowed_group(group_id):
    """Gruba izin ver"""
    if group_id not in permissions_data["allowed_groups"]:
        permissions_data["allowed_groups"].append(group_id)
        save_permissions()
        return True
    return False

def remove_allowed_group(group_id):
    """Grup iznini kaldır"""
    if group_id in permissions_data["allowed_groups"]:
        permissions_data["allowed_groups"].remove(group_id)
        save_permissions()
        return True
    return False

def block_user_in_group(user_id, group_id):
    """Kullanıcıyı belirli grupta engelle"""
    group_key = str(group_id)
    if group_key not in permissions_data["blocked_users"]:
        permissions_data["blocked_users"][group_key] = []
    if user_id not in permissions_data["blocked_users"][group_key]:
        permissions_data["blocked_users"][group_key].append(user_id)
        save_permissions()
        return True
    return False

def unblock_user_in_group(user_id, group_id):
    """Kullanıcının belirli gruptaki engelini kaldır"""
    group_key = str(group_id)
    if group_key in permissions_data["blocked_users"]:
        if user_id in permissions_data["blocked_users"][group_key]:
            permissions_data["blocked_users"][group_key].remove(user_id)
            save_permissions()
            return True
    return False

def check_permission(user_id, group_id):
    """Kullanıcının yetkisini kontrol et"""
    # Owner her zaman kullanabilir
    if user_id == OWNER_ID:
        return True
    
    # Private mode kapalıysa herkes kullanabilir
    if not private_mode.get(group_id, False):
        return True
    
    # Kullanıcı engelliyse kullanamaz
    group_key = str(group_id)
    if group_key in permissions_data["blocked_users"]:
        if user_id in permissions_data["blocked_users"][group_key]:
            return False
    
    # Kullanıcı izinliyse kullanabilir
    if user_id in permissions_data["allowed_users"]:
        return True
    
    # Grup izinliyse kullanabilir
    if group_id in permissions_data["allowed_groups"]:
        return True
    
    return False

# Yetkileri yükle
load_permissions()

# ================= YT-DLP AYARLARI =================
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

# ================= YARDIMCI FONKSİYONLAR =================

def format_duration(seconds):
    if not seconds or seconds == 0:
        return "00:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def create_progress_bar(current, total, length=12):
    if total == 0:
        return "▓" * length
    filled = int(length * current / total)
    if filled > length:
        filled = length
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

# ================= MESAJ GÖNDERİM =================

async def send_message(chat_id, text, reply_to=None):
    """Mesaj gönder - Bot grupta ise bot, değilse userbot"""
    global bot_client, userbot_client
    
    # Bot grupta mı?
    if await is_bot_in_group(chat_id):
        try:
            return await bot_client.send_message(chat_id, text, reply_to=reply_to)
        except:
            pass
    
    # Fallback: userbot
    if userbot_client:
        try:
            return await userbot_client.send_message(chat_id, text, reply_to=reply_to)
        except:
            pass
    
    return None

async def reply_message(event, text):
    """Event'e yanıt ver - Bot grupta ise bot, değilse userbot"""
    global bot_client, userbot_client
    chat_id = event.chat_id
    
    # Bot grupta mı?
    if await is_bot_in_group(chat_id):
        try:
            return await bot_client.send_message(chat_id, text, reply_to=event.id)
        except:
            pass
    
    # Fallback: userbot
    try:
        return await event.reply(text)
    except:
        pass
    
    return None

async def delete_message_safe(chat_id, msg):
    """Mesajı güvenli sil"""
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

# ================= BOT GRUP KONTROLÜ =================

async def is_bot_in_group(chat_id):
    """Bot'un grupta olup olmadığını kontrol et (cache'li)"""
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

async def bot_can_send_messages(chat_id):
    """Bot mesaj gönderebilir mi kontrol et"""
    if not await is_bot_in_group(chat_id):
        return False
    try:
        bot_me = await bot_client.get_me()
        perms = await bot_client.get_permissions(chat_id, bot_me.id)
        return perms.send_messages
    except:
        return False

# ================= PANEL FONKSİYONLARI =================

def create_panel_buttons(chat_id):
    """Panel butonları oluştur"""
    paused = is_paused.get(chat_id, False)
    elapsed = get_elapsed_time(chat_id)
    duration = 0
    is_live = False
    
    if chat_id in current_songs and current_songs[chat_id]:
        duration = current_songs[chat_id].get('duration', 0)
        is_live = current_songs[chat_id].get('is_live', False)
    
    if elapsed > duration and duration > 0:
        elapsed = duration
    
    if is_live:
        progress_text = "🔴 CANLI YAYIN"
    else:
        progress = create_progress_bar(elapsed, duration)
        progress_text = f"⏱ {format_duration(elapsed)} {progress} {format_duration(duration)}"
    
    if paused:
        return [
            [Button.inline(progress_text, f"np_{chat_id}")],
            [Button.inline("▶️ Devam", f"rs_{chat_id}"), Button.inline("⏹️ Bitir", f"st_{chat_id}")],
            [Button.inline("⏭️ Atla", f"sk_{chat_id}"), Button.inline("📋 Kuyruk", f"qu_{chat_id}")]
        ]
    else:
        return [
            [Button.inline(progress_text, f"np_{chat_id}")],
            [Button.inline("⏸️ Durdur", f"ps_{chat_id}"), Button.inline("⏹️ Bitir", f"st_{chat_id}")],
            [Button.inline("⏭️ Atla", f"sk_{chat_id}"), Button.inline("📋 Kuyruk", f"qu_{chat_id}")]
        ]

def create_panel_text(chat_id):
    """Panel metni oluştur"""
    if chat_id not in current_songs or not current_songs[chat_id]:
        return "🔇 Hiçbir şey çalmıyor."
    
    song = current_songs[chat_id]
    title = song.get('title', 'Bilinmeyen')
    paused = is_paused.get(chat_id, False)
    queue_count = len(music_queues.get(chat_id, []))
    requester = song.get('requester_name', 'Bilinmeyen')
    
    status_emoji = "⏸️" if paused else "🎵"
    status_text = "Duraklatıldı" if paused else "Çalıyor"
    
    return f"""{status_emoji} **{status_text}:** {title}

👤 **Talep:** {requester}
📋 **Kuyrukta:** {queue_count} şarkı"""

async def delete_panel_message(chat_id):
    """Panel mesajını sil"""
    global bot_client, userbot_client
    
    if chat_id not in current_songs or not current_songs[chat_id]:
        return
    
    msg_id = current_songs[chat_id].get('message_id')
    panel_msg = current_songs[chat_id].get('panel_message')
    
    if not msg_id and not panel_msg:
        return
    
    # Önce panel_msg ile dene
    if panel_msg:
        try:
            await panel_msg.delete()
            return
        except:
            pass
    
    # Bot ile dene
    if bot_client and msg_id:
        try:
            await bot_client.delete_messages(chat_id, msg_id)
            return
        except:
            pass
    
    # Userbot ile dene
    if userbot_client and msg_id:
        try:
            await userbot_client.delete_messages(chat_id, msg_id)
        except:
            pass

async def send_panel(chat_id):
    """Panel gönder - Bot grupta ise bot, değilse inline"""
    global userbot_client, bot_username, bot_client
    
    if not current_songs.get(chat_id):
        return None
    
    text = create_panel_text(chat_id)
    buttons = create_panel_buttons(chat_id)
    
    # Bot grupta mı kontrol et
    bot_available = await is_bot_in_group(chat_id)
    
    if bot_available and bot_client:
        # Bot ile gönder
        try:
            msg = await bot_client.send_message(chat_id, text, buttons=buttons)
            if msg and chat_id in current_songs and current_songs[chat_id]:
                current_songs[chat_id]['panel_message'] = msg
                current_songs[chat_id]['message_id'] = msg.id
                current_songs[chat_id]['sent_by_bot'] = True
            return msg
        except Exception as e:
            print(f"[PANEL] Bot gönderme hatası: {e}")
    
    # Inline query ile gönder (fallback)
    if userbot_client and bot_username:
        try:
            results = await userbot_client.inline_query(bot_username, f"panel_{chat_id}")
            if results:
                msg = await results[0].click(chat_id)
                if msg and chat_id in current_songs and current_songs[chat_id]:
                    current_songs[chat_id]['panel_message'] = msg
                    current_songs[chat_id]['message_id'] = msg.id
                    current_songs[chat_id]['sent_by_bot'] = False
                return msg
        except Exception as e:
            print(f"[PANEL] Inline panel hatası: {e}")
    
    return None

async def update_panel_message(chat_id):
    """Panel güncelle - Sadece bot grupta ise"""
    global bot_client
    
    if chat_id not in current_songs or not current_songs[chat_id]:
        return False
    
    song = current_songs[chat_id]
    msg_id = song.get('message_id')
    sent_by_bot = song.get('sent_by_bot', False)
    
    if not msg_id:
        return False
    
    # Sadece bot ile gönderilmişse güncelle
    if not sent_by_bot:
        return False
    
    text = create_panel_text(chat_id)
    buttons = create_panel_buttons(chat_id)
    
    if bot_client:
        try:
            await bot_client.edit_message(chat_id, msg_id, text, buttons=buttons)
            return True
        except Exception as e:
            err_str = str(e).upper()
            if "MESSAGE_NOT_MODIFIED" in err_str:
                return True
    
    return False

async def panel_updater_task(chat_id):
    """Panel güncelleme görevi"""
    try:
        while is_playing.get(chat_id) and chat_id in current_songs and current_songs[chat_id]:
            if not is_paused.get(chat_id, False):
                await update_panel_message(chat_id)
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[UPDATER] Hata: {e}")

def start_panel_updater(chat_id):
    """Panel güncelleme başlat"""
    global panel_update_tasks
    
    if chat_id in panel_update_tasks:
        try:
            panel_update_tasks[chat_id].cancel()
        except:
            pass
    
    async def safe_updater():
        await asyncio.sleep(3)
        await panel_updater_task(chat_id)
    
    task = asyncio.create_task(safe_updater())
    panel_update_tasks[chat_id] = task

def stop_panel_updater(chat_id):
    """Panel güncelleme durdur"""
    if chat_id in panel_update_tasks:
        try:
            panel_update_tasks[chat_id].cancel()
        except:
            pass
        del panel_update_tasks[chat_id]

# ================= GRUP & KATILIM =================

async def get_entity_safe(chat_id):
    try:
        entity = await music_client.get_entity(chat_id)
        return entity
    except:
        pass
    try:
        if userbot_client:
            entity = await userbot_client.get_entity(chat_id)
            return entity
    except:
        pass
    return None

async def is_assistant_in_chat(chat_id):
    cache_key = f"in_chat_{chat_id}"
    now = time.time()
    
    if cache_key in assistant_status_cache:
        cached_time, cached_result = assistant_status_cache[cache_key]
        if now - cached_time < CACHE_DURATION:
            return cached_result
    
    try:
        me = await music_client.get_me()
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
        'is_private': False,
        'is_supergroup': False,
        'has_join_request': False,
        'can_join': True,
        'invite_link': None,
        'entity': None,
        'username': None,
        'error': None
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
                result['username'] = entity.username
            else:
                result['is_private'] = True
            
            try:
                if userbot_client:
                    full = await userbot_client(GetFullChannelRequest(entity))
                    if hasattr(full.full_chat, 'join_request'):
                        result['has_join_request'] = full.full_chat.join_request
                    if hasattr(full.full_chat, 'exported_invite'):
                        if full.full_chat.exported_invite:
                            result['invite_link'] = full.full_chat.exported_invite.link
            except:
                pass
                
        elif isinstance(entity, Chat):
            result['is_private'] = True
            result['is_supergroup'] = False
            
    except ChannelPrivateError:
        result['is_private'] = True
        result['can_join'] = False
        result['error'] = 'private_no_access'
    except Exception as e:
        result['error'] = str(e)
    
    return result

async def check_userbot_admin_rights(chat_id):
    try:
        me = await userbot_client.get_me()
        participant = await userbot_client(GetParticipantRequest(chat_id, me.id))
        
        if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            if isinstance(participant.participant, ChannelParticipantCreator):
                return True, True
            if hasattr(participant.participant, 'admin_rights'):
                rights = participant.participant.admin_rights
                can_invite = rights.invite_users if hasattr(rights, 'invite_users') else False
                return True, can_invite
        return False, False
    except:
        return False, False

async def try_join_chat(chat_id, chat_info=None):
    if chat_info is None:
        chat_info = await check_chat_type(chat_id)
    
    entity = chat_info.get('entity')
    username = chat_info.get('username')
    
    if not entity:
        try:
            entity = await userbot_client.get_entity(chat_id)
            if hasattr(entity, 'username') and entity.username:
                username = entity.username
        except Exception as e:
            return False, f"❌ Grup bulunamadı: {e}"
    
    try:
        if isinstance(entity, Channel):
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
                        return False, "📝 Katılım isteği gönderildi, onaylayın."
            
            is_admin, can_invite = await check_userbot_admin_rights(chat_id)
            if can_invite:
                assistant_me = await music_client.get_me()
                try:
                    await userbot_client(InviteToChannelRequest(entity, [assistant_me.id]))
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Davet edildim!"
                except UserAlreadyParticipantError:
                    assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                    return True, "✅ Zaten gruptayım!"
                except Exception as e:
                    if "mutual" in str(e).lower():
                        return False, "❌ Gizlilik ayarları engel."
            
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
                except:
                    pass
            
            return False, "❌ Asistanı manuel ekleyin."
        
        elif isinstance(entity, Chat):
            try:
                assistant_me = await music_client.get_me()
                await userbot_client(AddChatUserRequest(chat_id, assistant_me.id, 100))
                assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                return True, "✅ Davet edildim!"
            except UserAlreadyParticipantError:
                assistant_status_cache[f"in_chat_{chat_id}"] = (time.time(), True)
                return True, "✅ Zaten gruptayım!"
            except Exception as e:
                return False, f"❌ Hata: {e}"
            
    except Exception as e:
        return False, f"❌ Katılım hatası: {str(e)}"
    
    return False, "❌ Bilinmeyen hata"

async def ensure_assistant_in_chat(chat_id):
    if await is_assistant_in_chat(chat_id):
        return True, None
    chat_info = await check_chat_type(chat_id)
    return await try_join_chat(chat_id, chat_info)

async def try_join_voice_chat(chat_id, stream):
    # py-tgcalls 2.x: join_group_call() ve change_stream() kaldirildi
    # play() her ikisinin gorevini yapıyor
    try:
        await pytgcalls.play(chat_id, stream)
        return True, None
    except Exception as e:
        error_str = str(e).lower()
        error_name = type(e).__name__
        if "noactivegroupcall" in error_name.lower() or "no active" in error_str:
            return False, "no_active_call"
        if "groupcallnotfound" in error_name.lower():
            return False, "no_active_call"
        if "not a member" in error_str or "participant" in error_str:
            return False, "need_join"
        return False, f"\u274c Sesli sohbet hatas\u0131: {e}"

# ================= TEMİZLİK =================

async def cleanup_music(chat_id, message=None, send_notification=True):
    global userbot_client
    
    stop_panel_updater(chat_id)
    await delete_panel_message(chat_id)
    
    if chat_id in music_queues:
        del music_queues[chat_id]
    if chat_id in download_status:
        del download_status[chat_id]
    if chat_id in download_tasks:
        for task in download_tasks[chat_id].values():
            try:
                task.cancel()
            except:
                pass
        del download_tasks[chat_id]
    
    is_playing[chat_id] = False
    is_paused[chat_id] = False
    current_songs[chat_id] = None
    
    if send_notification and message:
        await send_message(chat_id, f"📭 {message}")

# ================= İNDİRME =================

class DownloadStatus:
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

def get_download_emoji(status):
    emojis = {
        DownloadStatus.WAITING: "⏳",
        DownloadStatus.DOWNLOADING: "⬇️",
        DownloadStatus.PROCESSING: "🔄",
        DownloadStatus.READY: "✅",
        DownloadStatus.ERROR: "❌"
    }
    return emojis.get(status, "❓")

def update_download_status(chat_id, queue_index, status, progress=None):
    if chat_id not in download_status:
        download_status[chat_id] = {}
    download_status[chat_id][queue_index] = {
        'status': status,
        'progress': progress,
        'updated_at': time.time()
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
        result.append({
            **item,
            'download_status': status,
            'status_emoji': get_download_emoji(status)
        })
    return result

async def download_item(chat_id, item, queue_index):
    try:
        update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING)
        
        path = ""
        video_id = ""
        title = item.get('title', 'Bilinmeyen')
        duration = item.get('duration', 0)
        
        if item['type'] == 'tg':
            msg = item['data']
            video_id = f"tg_{msg.id}"
            path = f"/tmp/{video_id}.mp3"
            
            if not os.path.exists(path):
                update_download_status(chat_id, queue_index, DownloadStatus.DOWNLOADING, 50)
                await msg.download_media(file=path)
            
            if msg.audio and hasattr(msg.audio, 'duration'):
                duration = msg.audio.duration or duration
            elif msg.voice and hasattr(msg.voice, 'duration'):
                duration = msg.voice.duration or duration
            elif msg.document:
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
        
        elif item['type'] == 'yt':
            query = item['data']
            is_live = False
            stream_url = None
            
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': False, 'no_warnings': True}) as ydl:
                    search = query if "http" in query else f"ytsearch:{query}"
                    info = await asyncio.to_thread(ydl.extract_info, search, download=False)
                    
                    if not info:
                        raise Exception("Video bulunamadı")
                    
                    if 'entries' in info:
                        if not info['entries']:
                            raise Exception("Sonuç bulunamadı")
                        info = info['entries'][0]
                    
                    if not info.get('id'):
                        raise Exception("Video ID alınamadı")
                    
                    video_id = info['id']
                    title = info.get('title', 'YouTube')
                    duration = info.get('duration', 0) or 0
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    is_live = info.get('is_live', False) or info.get('live_status') == 'is_live'
                    
                    if is_live:
                        formats = info.get('formats', [])
                        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                        if audio_formats:
                            stream_url = audio_formats[-1].get('url')
                        else:
                            stream_url = info.get('url') or (formats[-1].get('url') if formats else None)
                        
                        if not stream_url:
                            raise Exception("Canlı yayın URL'i alınamadı")
                        
                        item['is_live'] = True
                        item['stream_url'] = stream_url
                        item['title'] = f"🔴 {title}"
                        item['duration'] = 0
                        item['path'] = stream_url
                        update_download_status(chat_id, queue_index, DownloadStatus.READY)
                        return True
                    
            except Exception as e:
                print(f"YouTube hatası: {e}")
                update_download_status(chat_id, queue_index, DownloadStatus.ERROR)
                return False
            
            path = f"/tmp/{video_id}.mp3"
            log_msg = await get_audio_from_log(video_id)
            
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
            item['path'] = path
            item['title'] = title
            item['duration'] = duration
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
            task = asyncio.create_task(download_item(chat_id, item, i))
            download_tasks[chat_id][i] = task

# ================= OYNATMA =================

async def play_logic(chat_id, item):
    path = item.get('path')
    title = item.get('title', 'Bilinmeyen')
    duration = item.get('duration', 0)
    is_live = item.get('is_live', False)
    stream_url = item.get('stream_url')

    if not is_live and (not path or not os.path.exists(path)):
        success = await download_item(chat_id, item, -1)
        if not success:
            return False, "İndirme başarısız", 0
        
        path = item.get('path')
        title = item.get('title', title)
        duration = item.get('duration', duration)
        is_live = item.get('is_live', False)
        stream_url = item.get('stream_url')

    if is_live:
        if not stream_url:
            return False, "Canlı yayın URL'i bulunamadı", 0
    else:
        if not path or not os.path.exists(path):
            return False, "Dosya bulunamadı", 0

    try:
        if is_live:
            stream = MediaStream(stream_url)
        else:
            stream = MediaStream(path)
        
        assistant_in_chat = await is_assistant_in_chat(chat_id)
        success, error_msg = await try_join_voice_chat(chat_id, stream)
        
        if not success:
            if error_msg in ("no_active_call", "need_join"):
                if not assistant_in_chat:
                    join_success, join_msg = await ensure_assistant_in_chat(chat_id)
                    if not join_success:
                        return False, join_msg, 0
                    await asyncio.sleep(0.5)
                    success, error_msg = await try_join_voice_chat(chat_id, stream)
                
                if not success:
                    if error_msg == "no_active_call":
                        return False, "❌ Aktif sesli sohbet yok! Önce başlatın.", 0
                    return False, error_msg or "Sesli sohbete katılamadım", 0
            else:
                return False, error_msg, 0

        is_playing[chat_id] = True
        is_paused[chat_id] = False
        
        current_songs[chat_id] = {
            'title': title,
            'duration': duration,
            'started_at': time.time(),
            'message_id': None,
            'chat_id': chat_id,
            'is_live': is_live,
            'requester_name': item.get('requester_name', 'Bilinmeyen'),
            'requester_id': item.get('requester_id')
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
        
        if chat_id in download_status:
            new_status = {}
            for i, status in download_status[chat_id].items():
                if i > 0:
                    new_status[i - 1] = status
            download_status[chat_id] = new_status
        
        # Bildirim mesajı gönder
        notify = await send_message(chat_id, f"⏭️ **Sıradaki:** `{next_item.get('title', 'Yükleniyor...')}`")
        
        await asyncio.sleep(1)
        
        if notify:
            await delete_message_safe(chat_id, notify)
        
        success, title, duration = await play_logic(chat_id, next_item)
        if not success:
            await next_song(chat_id)
    else:
        await send_message(chat_id, "📭 **Kuyruk bitti!**")
        
        try:
            await pytgcalls.leave_call(chat_id)
        except:
            pass
        
        is_playing[chat_id] = False
        is_paused[chat_id] = False
        current_songs[chat_id] = None
        
        if chat_id in music_queues:
            del music_queues[chat_id]

# ================= BAĞLANTI =================

async def init_music(api_id, api_hash):
    global music_client, pytgcalls, handlers_registered
    
    if music_client is None:
        music_client = TelegramClient(StringSession(MUSIC_SESSION), api_id, api_hash)
    
    if not music_client.is_connected():
        try:
            await music_client.start()
        except Exception as e:
            print(f"Music client hatası: {e}")
            return False

    if pytgcalls is None:
        pytgcalls = PyTgCalls(music_client)
    
    if not handlers_registered:
        # py-tgcalls >= 2.x: on_stream_end/on_left/on_kicked/on_closed_voice_chat artik yok
        # Hepsi on_update() + filtrelerle yapiliyor
        import pytgcalls.filters as pytgcalls_filters
        from pytgcalls.types import StreamEnded, ChatUpdate

        @pytgcalls.on_update(pytgcalls_filters.stream_end)
        async def on_stream_end(client, update):
            await next_song(update.chat_id)

        @pytgcalls.on_update(pytgcalls_filters.chat_update)
        async def on_chat_update(client, update):
            chat_id = update.chat_id
            status = getattr(update, 'status', None)
            if status == ChatUpdate.Status.LEFT_GROUP:
                if is_playing.get(chat_id) and current_songs.get(chat_id):
                    await cleanup_music(chat_id, "Sesli sohbet sonlandi.", True)
                else:
                    await cleanup_music(chat_id, None, False)
            elif status == ChatUpdate.Status.KICKED:
                if is_playing.get(chat_id) and current_songs.get(chat_id):
                    await cleanup_music(chat_id, "Sesli sohbetten atildum!", True)
                else:
                    await cleanup_music(chat_id, None, False)
            elif status == ChatUpdate.Status.CLOSED_VOICE_CHAT:
                if is_playing.get(chat_id) and current_songs.get(chat_id):
                    await cleanup_music(chat_id, "Sesli sohbet kapatildi.", True)
                else:
                    await cleanup_music(chat_id, None, False)

        handlers_registered = True
        try:
            await pytgcalls.start()
        except:
            pass

    return True

# ================= USERBOT KOMUTLARI =================

def register(client):
    global userbot_client, OWNER_ID
    userbot_client = client
    
    async def set_owner():
        global OWNER_ID
        me = await client.get_me()
        OWNER_ID = me.id
    
    client.loop.create_task(set_owner())

    @client.on(events.NewMessage(pattern=r'^\.cal(?:\s+(.+))?$'))
    async def play_handler(event):
        chat_id = event.chat_id
        sender = await event.get_sender()
        requester_name = sender.first_name if sender else "Bilinmeyen"
        requester_id = event.sender_id
        
        if not check_permission(event.sender_id, chat_id):
            return
            
        if not await init_music(client.api_id, client.api_hash):
            return await reply_message(event, "❌ Müzik bağlantısı kurulamadı.")
            
        query = event.pattern_match.group(1)
        reply = await event.get_reply_message()

        item = {}
        display_title = ""

        if reply and (reply.audio or reply.voice or (reply.document and reply.document.mime_type and 'audio' in reply.document.mime_type)):
            duration = 0
            if reply.audio and hasattr(reply.audio, 'duration'):
                duration = reply.audio.duration or 0
            elif reply.voice and hasattr(reply.voice, 'duration'):
                duration = reply.voice.duration or 0
            elif reply.document:
                for attr in reply.document.attributes:
                    if hasattr(attr, 'duration'):
                        duration = attr.duration or 0
                        break
            
            title = "Ses Dosyası"
            if reply.file and hasattr(reply.file, 'title') and reply.file.title:
                title = reply.file.title
            elif reply.audio and hasattr(reply.audio, 'title') and reply.audio.title:
                title = reply.audio.title
            
            item = {
                'type': 'tg', 
                'data': reply, 
                'title': title, 
                'duration': duration,
                'requester_name': requester_name,
                'requester_id': requester_id
            }
            display_title = title
        elif query:
            item = {
                'type': 'yt', 
                'data': query, 
                'title': query, 
                'duration': 0,
                'requester_name': requester_name,
                'requester_id': requester_id
            }
            display_title = query
        else:
            return await reply_message(event, "❌ Şarkı adı yaz veya ses dosyasına yanıt ver!")

        if is_playing.get(chat_id):
            if chat_id not in music_queues:
                music_queues[chat_id] = []
            
            queue_index = len(music_queues[chat_id])
            music_queues[chat_id].append(item)
            update_download_status(chat_id, queue_index, DownloadStatus.WAITING)
            
            msg = await reply_message(event, f"➕ **Kuyruğa eklendi**\n🎵 `{display_title}`\n👤 {requester_name}\n📋 Sıra: {queue_index + 1}")
            
            async def download_and_notify():
                success = await download_item(chat_id, item, queue_index)
                try:
                    if msg:
                        if success:
                            await msg.edit(
                                f"✅ **Hazır**\n🎵 `{item.get('title', display_title)}`\n👤 {requester_name}\n⏱ {format_duration(item.get('duration', 0))}"
                            )
                        else:
                            await msg.edit(f"❌ **İndirme başarısız**\n🎵 `{display_title}`")
                except:
                    pass
            
            asyncio.create_task(download_and_notify())
            return

        m = await reply_message(event, f"⚡ **Hazırlanıyor:** `{display_title}`")
        success, res, duration = await play_logic(chat_id, item)

        if success:
            await delete_message_safe(chat_id, m)
        else:
            if m:
                try:
                    await m.edit(f"❌ {res}")
                except:
                    pass

    @client.on(events.NewMessage(pattern=r'^\.atla$'))
    async def skip_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        if not is_playing.get(event.chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        
        sender = await event.get_sender()
        skipper_name = sender.first_name if sender else "Bilinmeyen"
        
        await reply_message(event, f"⏭️ **{skipper_name}** tarafından atlandı...")
        await next_song(event.chat_id)

    @client.on(events.NewMessage(pattern=r'^\.bitir$'))
    async def stop_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        
        chat_id = event.chat_id
        if not is_playing.get(chat_id):
            return await reply_message(event, "🔇 Şu an çalan yok.")
        
        sender = await event.get_sender()
        stopper_name = sender.first_name if sender else "Bilinmeyen"
        
        await cleanup_music(chat_id, None, False)
        try:
            await pytgcalls.leave_call(chat_id)
        except:
            pass
        
        await reply_message(event, f"⏹️ **{stopper_name}** tarafından durduruldu.")

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
            await pytgcalls.pause(chat_id)
            is_paused[chat_id] = True
            if chat_id in current_songs and current_songs[chat_id]:
                current_songs[chat_id]['paused_at'] = time.time()
            await update_panel_message(chat_id)
            await reply_message(event, "⏸️ Duraklatıldı.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

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
            await pytgcalls.resume(chat_id)
            if chat_id in current_songs and current_songs[chat_id]:
                paused_at = current_songs[chat_id].get('paused_at', time.time())
                started_at = current_songs[chat_id].get('started_at', time.time())
                pause_duration = time.time() - paused_at
                current_songs[chat_id]['started_at'] = started_at + pause_duration
            is_paused[chat_id] = False
            await update_panel_message(chat_id)
            await reply_message(event, "▶️ Devam ediliyor.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.kuyruk$'))
    async def queue_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        
        chat_id = event.chat_id
        queue_items = get_queue_with_status(chat_id)
        
        if queue_items:
            total_duration = sum(s.get('duration', 0) for s in queue_items)
            msg = "📋 **Kuyruk:**\n\n"
            for i, s in enumerate(queue_items[:10], 1):
                dur = format_duration(s.get('duration', 0))
                emoji = s.get('status_emoji', '⏳')
                requester = s.get('requester_name', '')
                msg += f"{emoji} **{i}.** {s['title'][:35]}"
                if s.get('duration'):
                    msg += f" `[{dur}]`"
                if requester:
                    msg += f" - {requester}"
                msg += "\n"
            
            if len(queue_items) > 10:
                msg += f"\n... ve {len(queue_items) - 10} şarkı daha"
            msg += f"\n\n⏱ Toplam: `{format_duration(total_duration)}`"
            await reply_message(event, msg)
        else:
            await reply_message(event, "📭 Kuyruk boş.")

    @client.on(events.NewMessage(pattern=r'^\.np$'))
    async def nowplaying_handler(event):
        if not check_permission(event.sender_id, event.chat_id):
            return
        
        chat_id = event.chat_id
        
        if chat_id in current_songs and current_songs[chat_id]:
            # Eski paneli sil ve yenisini gönder
            await delete_panel_message(chat_id)
            msg = await send_panel(chat_id)
            if msg:
                current_songs[chat_id]['message_id'] = msg.id
                current_songs[chat_id]['panel_message'] = msg
        else:
            await reply_message(event, "🔇 Şu an çalan yok.")

    # ================= ÖZEL MOD KOMUTLARI =================

    @client.on(events.NewMessage(pattern=r'^\.ozmod$'))
    async def private_on_handler(event):
        if event.sender_id != OWNER_ID:
            return
        chat_id = event.chat_id
        private_mode[chat_id] = True
        await reply_message(event, "🔒 **Özel mod AÇIK** - Sadece yetkili kullanıcılar kullanabilir.")

    @client.on(events.NewMessage(pattern=r'^\.ozmodkapat$'))
    async def private_off_handler(event):
        if event.sender_id != OWNER_ID:
            return
        chat_id = event.chat_id
        private_mode[chat_id] = False
        await reply_message(event, "🔓 **Özel mod KAPALI** - Herkes kullanabilir.")

    # ================= YETKİ KOMUTLARI =================

    @client.on(events.NewMessage(pattern=r'^\.izinver(?:\s+(.+))?$'))
    async def allow_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        arg = event.pattern_match.group(1)
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.izinver @kullanıcı` veya `.izinver grup_id`")
        
        # Yanıt verilen mesajdan kullanıcı al
        reply = await event.get_reply_message()
        if reply:
            user_id = reply.sender_id
            if add_allowed_user(user_id):
                await reply_message(event, f"✅ Kullanıcı `{user_id}` izin listesine eklendi.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten izinli.")
            return
        
        # @username veya ID
        try:
            if arg.startswith('@'):
                entity = await client.get_entity(arg)
                target_id = entity.id
            else:
                target_id = int(arg)
            
            # Negatif ise grup, pozitif ise kullanıcı
            if target_id < 0:
                if add_allowed_group(target_id):
                    await reply_message(event, f"✅ Grup `{target_id}` izin listesine eklendi.")
                else:
                    await reply_message(event, f"ℹ️ Grup zaten izinli.")
            else:
                if add_allowed_user(target_id):
                    await reply_message(event, f"✅ Kullanıcı `{target_id}` izin listesine eklendi.")
                else:
                    await reply_message(event, f"ℹ️ Kullanıcı zaten izinli.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.izinkaldir(?:\s+(.+))?$'))
    async def disallow_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if reply:
            user_id = reply.sender_id
            if remove_allowed_user(user_id):
                await reply_message(event, f"✅ Kullanıcı `{user_id}` izin listesinden çıkarıldı.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten izinli değil.")
            return
        
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.izinkaldir @kullanıcı` veya `.izinkaldir grup_id`")
        
        try:
            if arg.startswith('@'):
                entity = await client.get_entity(arg)
                target_id = entity.id
            else:
                target_id = int(arg)
            
            if target_id < 0:
                if remove_allowed_group(target_id):
                    await reply_message(event, f"✅ Grup `{target_id}` izin listesinden çıkarıldı.")
                else:
                    await reply_message(event, f"ℹ️ Grup zaten izinli değil.")
            else:
                if remove_allowed_user(target_id):
                    await reply_message(event, f"✅ Kullanıcı `{target_id}` izin listesinden çıkarıldı.")
                else:
                    await reply_message(event, f"ℹ️ Kullanıcı zaten izinli değil.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.engelle(?:\s+(.+))?$'))
    async def block_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        chat_id = event.chat_id
        arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if reply:
            user_id = reply.sender_id
            if block_user_in_group(user_id, chat_id):
                await reply_message(event, f"🚫 Kullanıcı `{user_id}` bu grupta engellendi.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten engelli.")
            return
        
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.engelle @kullanıcı` veya yanıt ver")
        
        try:
            if arg.startswith('@'):
                entity = await client.get_entity(arg)
                user_id = entity.id
            else:
                user_id = int(arg)
            
            if block_user_in_group(user_id, chat_id):
                await reply_message(event, f"🚫 Kullanıcı `{user_id}` bu grupta engellendi.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten engelli.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.engelkaldir(?:\s+(.+))?$'))
    async def unblock_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        chat_id = event.chat_id
        arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        if reply:
            user_id = reply.sender_id
            if unblock_user_in_group(user_id, chat_id):
                await reply_message(event, f"✅ Kullanıcı `{user_id}` engeli kaldırıldı.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten engelli değil.")
            return
        
        if not arg:
            return await reply_message(event, "❌ Kullanım: `.engelkaldir @kullanıcı` veya yanıt ver")
        
        try:
            if arg.startswith('@'):
                entity = await client.get_entity(arg)
                user_id = entity.id
            else:
                user_id = int(arg)
            
            if unblock_user_in_group(user_id, chat_id):
                await reply_message(event, f"✅ Kullanıcı `{user_id}` engeli kaldırıldı.")
            else:
                await reply_message(event, f"ℹ️ Kullanıcı zaten engelli değil.")
        except Exception as e:
            await reply_message(event, f"❌ Hata: {e}")

    @client.on(events.NewMessage(pattern=r'^\.izinliste$'))
    async def permissions_list_handler(event):
        if event.sender_id != OWNER_ID:
            return
        
        msg = "📋 **İzin Listesi:**\n\n"
        
        if permissions_data["allowed_users"]:
            msg += "👤 **İzinli Kullanıcılar:**\n"
            for uid in permissions_data["allowed_users"]:
                msg += f"  • `{uid}`\n"
        else:
            msg += "👤 **İzinli Kullanıcılar:** Yok\n"
        
        msg += "\n"
        
        if permissions_data["allowed_groups"]:
            msg += "👥 **İzinli Gruplar:**\n"
            for gid in permissions_data["allowed_groups"]:
                msg += f"  • `{gid}`\n"
        else:
            msg += "👥 **İzinli Gruplar:** Yok\n"
        
        msg += "\n"
        
        if permissions_data["blocked_users"]:
            msg += "🚫 **Engelli Kullanıcılar:**\n"
            for gid, users in permissions_data["blocked_users"].items():
                if users:
                    msg += f"  Grup `{gid}`:\n"
                    for uid in users:
                        msg += f"    • `{uid}`\n"
        else:
            msg += "🚫 **Engelli Kullanıcılar:** Yok\n"
        
        await reply_message(event, msg)

    @client.on(events.NewMessage(pattern=r'^\.muzikhelp$'))
    async def help_handler(event):
        await reply_message(event, """🎵 **MÜZİK KOMUTLARI**

**Temel:**
`.cal <şarkı>` - Çal veya kuyruğa ekle
`.atla` - Sonraki şarkı
`.bitir` - Durdur ve çık
`.durdur` - Durakla
`.devam` - Devam et

**Bilgi:**
`.kuyruk` - Kuyruk listesi
`.np` - Şu an çalan (panel yenile)

**Özel Mod:**
`.ozmod` - Özel mod aç
`.ozmodkapat` - Özel mod kapat

**Yetki (Sahip):**
`.izinver @kullanıcı/grup_id` - İzin ver
`.izinkaldir @kullanıcı/grup_id` - İzin kaldır
`.engelle @kullanıcı` - Grupta engelle
`.engelkaldir @kullanıcı` - Engel kaldır
`.izinliste` - İzin listesi
""")

# ================= BOT KOMUTLARI =================

def register_bot(bot, client):
    global bot_username, bot_client
    bot_client = bot
    
    async def set_name():
        global bot_username
        me = await bot.get_me()
        bot_username = me.username
    
    bot.loop.create_task(set_name())

    @bot.on(events.InlineQuery(pattern=r'^panel_(-?\d+)$'))
    async def panel_inline_handler(event):
        chat_id = int(event.pattern_match.group(1))
        
        if not current_songs.get(chat_id) or not is_playing.get(chat_id):
            return
        
        text = create_panel_text(chat_id)
        buttons = create_panel_buttons(chat_id)
        
        await event.answer([
            event.builder.article(
                title="🎵 Müzik Paneli",
                description=f"Çalıyor: {current_songs[chat_id].get('title', 'Bilinmeyen')}",
                text=text,
                buttons=buttons
            )
        ], cache_time=0)

    @bot.on(events.CallbackQuery())
    async def callback_handler(event):
        data = event.data.decode()
        
        try:
            parts = data.split("_")
            action = parts[0]
            chat_id = int(parts[1])
            
            if action == "ps":  # Durdur
                if is_playing.get(chat_id) and not is_paused.get(chat_id):
                    try:
                        await pytgcalls.pause(chat_id)
                        is_paused[chat_id] = True
                        if chat_id in current_songs and current_songs[chat_id]:
                            current_songs[chat_id]['paused_at'] = time.time()
                        
                        text = create_panel_text(chat_id)
                        buttons = create_panel_buttons(chat_id)
                        await event.edit(text, buttons=buttons)
                        await event.answer("⏸️ Duraklatıldı", alert=False)
                    except Exception as e:
                        await event.answer(f"Hata: {e}", alert=True)
                else:
                    await event.answer("Zaten duraklatılmış", alert=False)
            
            elif action == "rs":  # Devam
                if is_playing.get(chat_id) and is_paused.get(chat_id):
                    try:
                        await pytgcalls.resume(chat_id)
                        if chat_id in current_songs and current_songs[chat_id]:
                            paused_at = current_songs[chat_id].get('paused_at', time.time())
                            started_at = current_songs[chat_id].get('started_at', time.time())
                            pause_duration = time.time() - paused_at
                            current_songs[chat_id]['started_at'] = started_at + pause_duration
                        is_paused[chat_id] = False
                        
                        text = create_panel_text(chat_id)
                        buttons = create_panel_buttons(chat_id)
                        await event.edit(text, buttons=buttons)
                        await event.answer("▶️ Devam", alert=False)
                    except Exception as e:
                        await event.answer(f"Hata: {e}", alert=True)
                else:
                    await event.answer("Zaten çalıyor", alert=False)
            
            elif action == "sk":  # Atla
                try:
                    user = await event.get_sender()
                    skipper_name = user.first_name if user else "Bilinmeyen"
                except:
                    skipper_name = "Bilinmeyen"
                
                await event.answer("⏭️ Atlanıyor...", alert=False)
                await send_message(chat_id, f"⏭️ **{skipper_name}** tarafından atlandı...")
                await next_song(chat_id)
            
            elif action == "st":  # Bitir
                try:
                    user = await event.get_sender()
                    stopper_name = user.first_name if user else "Bilinmeyen"
                except:
                    stopper_name = "Bilinmeyen"
                
                try:
                    await event.delete()
                except:
                    pass
                
                await cleanup_music(chat_id, None, False)
                try:
                    await pytgcalls.leave_call(chat_id)
                except:
                    pass
                
                await event.answer("⏹️ Durduruldu", alert=False)
                await send_message(chat_id, f"⏹️ **{stopper_name}** tarafından durduruldu.")
            
            elif action == "qu":  # Kuyruk
                queue_items = get_queue_with_status(chat_id)
                if queue_items:
                    queue_list = "\n".join([
                        f"{s['status_emoji']} {i}. {s['title'][:25]}"
                        for i, s in enumerate(queue_items[:5], 1)
                    ])
                    extra = f"\n... +{len(queue_items) - 5}" if len(queue_items) > 5 else ""
                    await event.answer(f"📋 Kuyruk:\n{queue_list}{extra}", alert=True)
                else:
                    await event.answer("📭 Kuyruk boş", alert=True)
            
            elif action == "np":  # İlerleme çubuğu tıklandı
                await event.answer("🎵 Çalıyor...", alert=False)
                    
        except Exception as e:
            await event.answer("Hata oluştu", alert=False)
            print(f"Callback hatası: {e}")
