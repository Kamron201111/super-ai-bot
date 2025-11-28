import os
import telebot
import yt_dlp
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Replit/GitHub uchun
bot = telebot.TeleBot(BOT_TOKEN)

# YouTube qidiruv funksiyasi
def search_youtube(query):
    try:
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        html = requests.get(url).text

        video_ids = []
        titles = []

        # videolarni ajratib olish
        while 'videoId":"' in html and len(video_ids) < 10:
            idx = html.index('videoId":"') + 10
            vid = html[idx:idx+11]
            if vid not in video_ids:
                video_ids.append(vid)
            html = html[idx+11:]

        # sarlavhalar
        html = requests.get(url).text
        while '"title":{"runs":[{"text":"' in html and len(titles) < 10:
            idx = html.index('"title":{"runs":[{"text":"') + 26
            title = html[idx: html.index('"}]', idx)]
            titles.append(title)
            html = html[idx+10:]

        results = []
        for i in range(min(len(video_ids), len(titles))):
            results.append((titles[i], video_ids[i]))

        return results

    except:
        return []

# MP3 yuklash funksiyasi
def download_mp3(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': 'music.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return "music.mp3"
    except Exception as e:
        print("Download error:", e)
        return None

# START
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, 
                 "🎵 *Music Search Bot*\n"
                 "Qo‘shiq nomini yozing, men sizga 10 ta variant topib beraman.",
                 parse_mode="Markdown")

# INLINE tugmalar orqali musiqa yuborish
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    video_id = call.data

    bot.answer_callback_query(call.id, "Yuklanmoqda... ⏳")
    mp3 = download_mp3(video_id)

    if mp3:
        bot.send_audio(call.message.chat.id, open(mp3, "rb"))
    else:
        bot.send_message(call.message.chat.id, "❌ Yuklab bo‘lmadi.")

# MATN (musiqa nomi)
@bot.message_handler(func=lambda m: True)
def music_search(msg):
    query = msg.text.strip()
    bot.reply_to(msg, "🔍 Qidirilmoqda...")

    results = search_youtube(query)

    if not results:
        bot.reply_to(msg, "❌ Hech narsa topilmadi.")
        return

    # Inline tugmalar
    keyboard = telebot.types.InlineKeyboardMarkup()

    for i, (title, vid) in enumerate(results, start=1):
        btn = telebot.types.InlineKeyboardButton(
            text=f"{i}. {title[:40]}",
            callback_data=vid
        )
        keyboard.add(btn)

    bot.send_message(msg.chat.id, "🎶 *Topilgan qo‘shiqlar:*\nVariantlardan birini tanlang:",
                     reply_markup=keyboard, parse_mode="Markdown")

# Botni ishga tushirish
bot.infinity_polling()
