import os
import json
import yt_dlp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from youtube_search import YoutubeSearch

# ================== الإعدادات الأساسية ==================
API_ID = 20938788
API_HASH = "f6e8b15641bbf5f30877f965e4be56c0"
TOKEN = "8505423818:AAEJ1bywnkgtQkzTl_ENOa_NNW2mEZgmHFQ"
OWNER_ID = 5008284582
CHANNEL_USER = "JJ_5G"

name_bot = "DJ MAX"
username_bot = "MYDJMAX_BOT"

app = Client("DJ_MAX_PRO", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

# ================== قاعدة البيانات ==================
DB_FILE = "bot_data.json"
def load_db():
    if not os.path.exists(DB_FILE): return {"users": [], "groups": [], "banned": [], "maintenance": False}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"users": [], "groups": [], "banned": [], "maintenance": False}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_db()

# ================== وظائف المساعدة ==================
async def is_subscribed(uid):
    if uid == OWNER_ID: return True
    try:
        await app.get_chat_member(CHANNEL_USER, uid)
        return True
    except: return False

def check_youtube():
    if not os.path.exists("check-youtube.json"):
        with open("check-youtube.json", "w") as f: json.dump({"check":"True"}, f)
    with open("check-youtube.json") as f: return json.load(f)["check"] == "True"

# ================== الفلاتر والتحكم والإشعارات ==================
@app.on_message(group=-1)
async def bot_filters(client, message):
    if not message.from_user: return
    uid = message.from_user.id
    
    if message.chat.type == enums.ChatType.PRIVATE:
        if uid not in db["users"]:
            db["users"].append(uid)
            save_db(db)
            try:
                user = message.from_user
                chat_info = await client.get_chat(uid)
                count = len(db["users"])
                msg_text = (f"🔔 **مستخدم جديد دخل للبوت!**\n\n👤 **الاسم:** {user.mention}\n🆔 **الايدي:** `{uid}`\n🔗 **اليوزر:** @{user.username or 'لا يوجد'}\n📄 **البايو:** {chat_info.bio or 'لا يوجد'}\n🔢 **ترتيبه في البوت:** {count}")
                async for photo in client.get_chat_photos(uid, limit=1):
                    await client.send_photo(OWNER_ID, photo.file_id, caption=msg_text)
                    break
                else: await client.send_message(OWNER_ID, msg_text)
            except: pass
    else:
        if message.chat.id not in db["groups"]:
            db["groups"].append(message.chat.id)
            save_db(db)

    if uid in db["banned"]: await message.stop_propagation()
    if db.get("maintenance") and uid != OWNER_ID: await message.stop_propagation()
    if message.chat.type == enums.ChatType.PRIVATE and not await is_subscribed(uid):
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("اشترك في القناة ✅", url=f"t.me/{CHANNEL_USER}")]])
        await message.reply(f"⚠️ عذراً عزيزي، يجب عليك الاشتراك في قناة البوت أولاً.\nبعد الاشتراك، أرسل /start مجدداً.", reply_markup=btn)
        await message.stop_propagation()

# ================== أمر البداية (START) ==================
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    user = message.from_user
    chat_info = await app.get_chat(uid)
    
    caption = (f"👤 **الاسم:** {user.first_name}\n🆔 **الايدي:** `{uid}`\n🔗 **اليوزر:** @{user.username or 'لا يوجد'}\n📄 **البايو:** {chat_info.bio or 'لا يوجد'}\n\n"
               f"مرحباً بك {user.first_name} في بوت {name_bot} 🎵\n"
               f"أرسل **(بحث + الاسم)** للتحميل بالاختيار\n"
               f"أرسل **(يوت + الاسم)** للتحميل صوت فوراً")

    btns = [[InlineKeyboardButton("➕ اضفني لمجموعتك", url=f"https://t.me/{app.me.username}?startgroup=true")],
            [InlineKeyboardButton("ℹ️ معلوماتي", callback_data="myinfo"), InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/V7_N7")]]
    
    if uid == OWNER_ID:
        btns.insert(0, [InlineKeyboardButton("📊 الاحصائيات", callback_data="stats"), InlineKeyboardButton("🛠 الصيانة", callback_data="toggle_main")])

    async for photo in app.get_chat_photos(uid, limit=1):
        return await message.reply_photo(photo.file_id, caption=caption, reply_markup=InlineKeyboardMarkup(btns))
    await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(btns))

# ================== نظام يوت (تحميل صوت فوري - بدون FFmpeg) ==================
@app.on_message(filters.regex(r"^(يوت|YT)\s+(.*)"))
async def quick_audio(client, message):
    if not check_youtube(): return await message.reply("⇜ اليوتيوب معطل.")
    query = message.matches[0].group(2)
    wait = await message.reply("🔍 جاري التحميل المباشر...")
    try:
        search = YoutubeSearch(query, max_results=1).to_dict()
        if not search: return await wait.edit("❌ لم يتم العثور على نتائج.")
        
        vid_id = search[0]['id']
        url = f"https://youtu.be/{vid_id}"
        # نستخدم التنسيق اللي ما يطلب FFmpeg
        ydl_opts = {"format": "bestaudio[ext=m4a]", "outtmpl": f"downloads/%(id)s.%(ext)s", "quiet": True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        caption = f"🎬 **{info['title']}**\n⏱ **الوقت:** {info.get('duration_string')}\n\n✅ تم التحميل بواسطة @{username_bot}"
        await message.reply_audio(audio=file_path, title=info.get('title'), performer=name_bot, caption=caption)
        await wait.delete()
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e: await wait.edit(f"❌ خطأ: {e}")

# ================== نظام بحث (أزرار واختيار) ==================
@app.on_message(filters.regex(r"^بحث\s+(.*)"))
async def search_yt(client, message):
    query = message.matches[0].group(1)

    # 🔎 رد جاري البحث
    wait_msg = await message.reply(f"🔎 جاري البحث عن: {query} ...")

    res = YoutubeSearch(query, max_results=5).to_dict()

    if not res:
        return await wait_msg.edit_text("❌ لم يتم العثور على نتائج.")

    buttons = []
    for r in res:
        buttons.append([
            InlineKeyboardButton(
                f"🎬 {r['title'][:35]}..",
                callback_data=f"opt|{r['id']}"
            )
        ])

    # ✨ تعديل نفس رسالة "جاري البحث" بدل إرسال وحدة جديدة
    await wait_msg.edit_text(
        f"🔎 نتائج البحث عن: **{query}**\n\nإختر المقطع المطلوب:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^opt\|(.*)"))
async def choice_panel(client, query: CallbackQuery):
    vid = query.data.split("|")[1]
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("صوت 🎵", callback_data=f"down|m4a|{vid}"), InlineKeyboardButton("فيديو 🎥", callback_data=f"down|mp4|{vid}")]])
    await query.message.edit("إختر نوع التحميل:", reply_markup=markup)

@app.on_callback_query(filters.regex(r"^down\|(.*)"))
async def download_exec(client, query: CallbackQuery):
    _, ftype, vid = query.data.split("|")
    url = f"https://youtu.be/{vid}"
    await query.message.edit("⏳ جاري التحميل...")
    try:
        # الإعدادات الآمنة التي لا تحتاج FFmpeg
        ydl_opts = {"format": "bestaudio[ext=m4a]" if ftype=="m4a" else "best[ext=mp4]/best", "outtmpl": f"downloads/{vid}.%(ext)s", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        caption = f"🎬 **{info['title']}**\n⏱ **الوقت:** {info.get('duration_string')}\n\n✅ بواسطة @{username_bot}"
        if ftype == 'm4a': await query.message.reply_audio(file_path, title=info['title'], caption=caption)
        else: await query.message.reply_video(file_path, caption=caption)
        
        await query.message.delete()
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e: await query.message.edit(f"❌ خطأ: {e}")

# ================== أوامر الإدارة ==================
@app.on_message(filters.command("اذعة") & filters.user(OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message: return await message.reply("رد على رسالة.")
    count = 0
    for user_id in db["users"]:
        try:
            await message.reply_to_message.copy(user_id)
            count += 1
        except: pass
    await message.reply(f"✅ تمت الإذاعة لـ {count}")

@app.on_callback_query()
async def general_callbacks(client, query: CallbackQuery):
    uid = query.from_user.id
    if query.data == "stats" and uid == OWNER_ID:
        await query.answer(f"📊 المستخدمين: {len(db['users'])}\n👥 المجموعات: {len(db['groups'])}", show_alert=True)
    elif query.data == "toggle_main" and uid == OWNER_ID:
        db["maintenance"] = not db.get("maintenance"); save_db(db)
        await query.answer(f"🛠 وضع الصيانة: {'تعمل' if db['maintenance'] else 'مطفاة'}", show_alert=True)
    elif query.data == "myinfo":
        await query.message.reply(f"👤 الاسم: {query.from_user.first_name}\n🆔 الايدي: `{uid}`")

if __name__ == "__main__":
    if not os.path.exists("downloads"): os.makedirs("downloads")
    print("✅ DJ MAX PRO FINAL IS ONLINE!")
    app.run()
