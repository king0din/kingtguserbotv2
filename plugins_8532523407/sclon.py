# KingTG UserBot - Klon Plugin
# Profil klonlama - Çoklu fotoğraf ve video desteği
# Her hesap için ayrı veri tutulur

import os
from telethon import events
from telethon.tl.functions.photos import GetUserPhotosRequest, DeletePhotosRequest, UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateEmojiStatusRequest, UpdateProfileRequest
from telethon.tl.types import InputPhoto, EmojiStatus, EmojiStatusEmpty

# Görünmez emoji ID
INVISIBLE_EMOJI_ID = 5420560971674435677

# Her hesap için ayrı profil verisi {user_id: {...}}
USER_PROFILES = {}


def get_user_dirs(user_id):
    """Kullanıcının dizinlerini döndür"""
    temp_dir = f"/tmp/klon_temp_{user_id}"
    orig_dir = f"/tmp/klon_original_{user_id}"
    for d in [temp_dir, orig_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
    return temp_dir, orig_dir


def get_profile(user_id):
    """Kullanıcının profil verisini al veya oluştur"""
    if user_id not in USER_PROFILES:
        USER_PROFILES[user_id] = {
            "first_name": None,
            "last_name": None,
            "about": None,
            "photos": [],
            "emoji_status": None,
            "is_saved": False
        }
    return USER_PROFILES[user_id]


async def download_all_photos(client, user_id, save_dir, prefix="photo"):
    """Tüm profil fotoğraflarını indir"""
    photos_info = []
    try:
        result = await client(GetUserPhotosRequest(user_id=user_id, offset=0, max_id=0, limit=100))
        if not result.photos:
            return photos_info
        
        for idx, photo in enumerate(result.photos):
            try:
                is_video = hasattr(photo, 'video_sizes') and photo.video_sizes
                ext = ".mp4" if is_video else ".jpg"
                file_path = os.path.join(save_dir, f"{prefix}_{idx}{ext}")
                
                downloaded = await client.download_media(photo, file=file_path)
                if downloaded:
                    photos_info.append((downloaded, is_video))
            except:
                continue
    except:
        pass
    return photos_info


async def delete_my_photos(client):
    """Tüm profil fotoğraflarımı sil"""
    try:
        while True:
            photos = await client(GetUserPhotosRequest(user_id="me", offset=0, max_id=0, limit=100))
            if not photos.photos:
                break
            input_photos = [InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference) for p in photos.photos]
            if input_photos:
                await client(DeletePhotosRequest(id=input_photos))
            else:
                break
    except:
        pass


async def get_target_user(client, event, input_str=None):
    """Hedef kullanıcıyı bul"""
    if event.reply_to_msg_id:
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            try:
                user = await client(GetFullUserRequest(reply.sender_id))
                return user, None
            except Exception as e:
                return None, f"Kullanıcı bulunamadı: {e}"
    
    if input_str:
        input_str = input_str.strip().lstrip('@')
        
        if input_str.isdigit():
            try:
                user = await client(GetFullUserRequest(int(input_str)))
                return user, None
            except Exception as e:
                return None, f"ID bulunamadı: {e}"
        
        try:
            entity = await client.get_entity(input_str)
            user = await client(GetFullUserRequest(entity.id))
            return user, None
        except Exception as e:
            return None, f"Kullanıcı bulunamadı: {e}"
    
    return None, "Kullanıcı belirtilmedi"


def register(client):
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.klon(?:\s+(.+))?$'))
    async def klon_cmd(event):
        # Bu client'ın sahibinin ID'sini al
        me = await client.get_me()
        my_id = me.id
        profile = get_profile(my_id)
        temp_dir, orig_dir = get_user_dirs(my_id)
        
        input_str = event.pattern_match.group(1)
        
        if not input_str and not event.reply_to_msg_id:
            return await event.edit(
                "**🎭 Klon Plugin**\n\n"
                "**Kullanım:**\n"
                "• `.klon @kullanıcı`\n"
                "• `.klon 123456789`\n"
                "• Mesaja yanıt + `.klon`\n\n"
                "**Diğer:**\n"
                "• `.unclon` - Orijinale dön\n"
                "• `.saveme` - Profilini kaydet\n"
                "• `.kloninfo` - Kayıtlı profil\n"
                "• `.resetklon` - Sıfırla"
            )
        
        await event.edit("🔄 **Klonlanıyor...**")
        
        # Orijinal profili kaydet (ilk kez)
        if not profile["is_saved"]:
            try:
                await event.edit("📸 **Orijinal profil kaydediliyor...**")
                
                my_full = await client(GetFullUserRequest(my_id))
                
                profile["first_name"] = me.first_name or ""
                profile["last_name"] = me.last_name or ""
                profile["about"] = my_full.full_user.about if hasattr(my_full, 'full_user') else ""
                
                for f in os.listdir(orig_dir):
                    try:
                        os.remove(os.path.join(orig_dir, f))
                    except:
                        pass
                
                profile["photos"] = await download_all_photos(client, my_id, orig_dir, "orig")
                
                if hasattr(me, 'emoji_status') and me.emoji_status and hasattr(me.emoji_status, 'document_id'):
                    profile["emoji_status"] = me.emoji_status.document_id
                else:
                    profile["emoji_status"] = None
                
                profile["is_saved"] = True
                
            except Exception as e:
                return await event.edit(f"❌ **Profil kaydedilemedi:** `{e}`")
        
        target, error = await get_target_user(client, event, input_str)
        
        if not target:
            return await event.edit(f"❌ **{error}**")
        
        try:
            if hasattr(target, 'users') and target.users:
                user = target.users[0]
            elif hasattr(target, 'user'):
                user = target.user
            else:
                return await event.edit("❌ **Kullanıcı bilgisi alınamadı!**")
            
            user_id = user.id
            first_name = (user.first_name or "").replace("\u2060", "")
            last_name = (user.last_name or "").replace("\u2060", "")
            bio = target.full_user.about if hasattr(target, 'full_user') and target.full_user.about else ""
            
            for f in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, f))
                except:
                    pass
            
            await event.edit("📥 **Fotoğraflar indiriliyor...**")
            target_photos = await download_all_photos(client, user_id, temp_dir, "clone")
            
            await event.edit("✏️ **Profil güncelleniyor...**")
            await client(UpdateProfileRequest(first_name=first_name, last_name=last_name, about=bio))
            
            await delete_my_photos(client)
            
            if target_photos:
                await event.edit("📤 **Fotoğraflar yükleniyor...**")
                for photo_path, is_video in reversed(target_photos):
                    if os.path.exists(photo_path):
                        try:
                            pfile = await client.upload_file(photo_path)
                            if is_video:
                                await client(UploadProfilePhotoRequest(video=pfile))
                            else:
                                await client(UploadProfilePhotoRequest(file=pfile))
                        except:
                            pass
            
            emoji_msg = ""
            try:
                if hasattr(user, 'emoji_status') and user.emoji_status and hasattr(user.emoji_status, 'document_id'):
                    await client(UpdateEmojiStatusRequest(emoji_status=EmojiStatus(document_id=user.emoji_status.document_id)))
                    emoji_msg = " 😀✓"
                else:
                    await client(UpdateEmojiStatusRequest(emoji_status=EmojiStatus(document_id=INVISIBLE_EMOJI_ID)))
                    emoji_msg = " 😀👻"
            except:
                pass
            
            photo_count = len(target_photos)
            await event.edit(f"✅ **Klonlandı!** ({photo_count} fotoğraf{emoji_msg})")
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.unclon$'))
    async def unclon_cmd(event):
        me = await client.get_me()
        my_id = me.id
        profile = get_profile(my_id)
        
        if not profile["is_saved"]:
            return await event.edit("❌ **Kayıtlı profil yok!** Önce birini klonla.")
        
        await event.edit("🔄 **Orijinale dönülüyor...**")
        
        try:
            await client(UpdateProfileRequest(
                first_name=profile["first_name"],
                last_name=profile["last_name"],
                about=profile["about"] or ""
            ))
            
            await delete_my_photos(client)
            
            uploaded = 0
            if profile["photos"]:
                for photo_path, is_video in reversed(profile["photos"]):
                    if os.path.exists(photo_path):
                        try:
                            pfile = await client.upload_file(photo_path)
                            if is_video:
                                await client(UploadProfilePhotoRequest(video=pfile))
                            else:
                                await client(UploadProfilePhotoRequest(file=pfile))
                            uploaded += 1
                        except:
                            pass
            
            try:
                if profile["emoji_status"]:
                    await client(UpdateEmojiStatusRequest(emoji_status=EmojiStatus(document_id=profile["emoji_status"])))
                else:
                    await client(UpdateEmojiStatusRequest(emoji_status=EmojiStatusEmpty()))
            except:
                pass
            
            await event.edit(f"✅ **Orijinal profile döndün!** ({uploaded} fotoğraf)")
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.saveme$'))
    async def saveme_cmd(event):
        me = await client.get_me()
        my_id = me.id
        profile = get_profile(my_id)
        _, orig_dir = get_user_dirs(my_id)
        
        await event.edit("🔄 **Profil kaydediliyor...**")
        
        try:
            my_full = await client(GetFullUserRequest(my_id))
            
            profile["first_name"] = me.first_name or ""
            profile["last_name"] = me.last_name or ""
            profile["about"] = my_full.full_user.about if hasattr(my_full, 'full_user') else ""
            
            for f in os.listdir(orig_dir):
                try:
                    os.remove(os.path.join(orig_dir, f))
                except:
                    pass
            
            profile["photos"] = await download_all_photos(client, my_id, orig_dir, "orig")
            
            if hasattr(me, 'emoji_status') and me.emoji_status and hasattr(me.emoji_status, 'document_id'):
                profile["emoji_status"] = me.emoji_status.document_id
            else:
                profile["emoji_status"] = None
            
            profile["is_saved"] = True
            
            photo_count = len(profile["photos"])
            bio = profile['about'][:30] + "..." if len(profile['about'] or "") > 30 else (profile['about'] or "(boş)")
            
            await event.edit(
                f"✅ **Profil kaydedildi!**\n\n"
                f"👤 `{profile['first_name']} {profile['last_name']}`\n"
                f"📝 `{bio}`\n"
                f"📷 `{photo_count} fotoğraf`"
            )
            
        except Exception as e:
            await event.edit(f"❌ **Hata:** `{e}`")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.kloninfo$'))
    async def kloninfo_cmd(event):
        me = await client.get_me()
        my_id = me.id
        profile = get_profile(my_id)
        
        if not profile["is_saved"]:
            return await event.edit("❌ **Kayıtlı profil yok!**")
        
        photo_count = len(profile["photos"])
        bio = profile['about'] if profile['about'] else "(boş)"
        emoji = "✓" if profile["emoji_status"] else "yok"
        
        await event.edit(
            f"📋 **Kayıtlı Profil**\n\n"
            f"👤 `{profile['first_name']} {profile['last_name']}`\n"
            f"📝 `{bio}`\n"
            f"📷 `{photo_count}` 😀 `{emoji}`"
        )

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.resetklon$'))
    async def resetklon_cmd(event):
        me = await client.get_me()
        my_id = me.id
        profile = get_profile(my_id)
        
        for photo_path, _ in profile.get("photos", []):
            if photo_path and os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass
        
        USER_PROFILES[my_id] = {
            "first_name": None,
            "last_name": None,
            "about": None,
            "photos": [],
            "emoji_status": None,
            "is_saved": False
        }
        
        await event.edit("✅ **Klon verileri sıfırlandı!**")