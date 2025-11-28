import os
import telebot
import requests
import yt_dlp

# Token Replit/GitHub Secretsdan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ========== 1) YouTube qidiruv (10 ta variant) ==========
def search_youtube(query):
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': True,
            'default_search': 'ytsearch10'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)

        results = []
        for entry in info.get('entries', []):
            title = entry.get("title")
            video_id = entry.get("id")

            if title and video_id:
                results.append((title, video_id))

        return results

    except Exception as e:
        print("Search Error:", e)
        return []


# ========== 2) MP3 yuklab beruvchi FUNKSIYA ==========
def download_mp3(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'music.%(ext)s',
            'quiet': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        return "music.mp3"

    except Exception as e:
        print("Download Error >>>", e)
        return None


# ========== 3) /start buyrug'i ==========
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "🎵 *Super Music Bot*\n"
        "Qo‘shiq nomini yozing.\n"
        "Men sizga 10 ta variant chiqaraman 🎧",
        parse_mode="Markdown"
    )


# ========== 4) Inline tugma bosilganda MP3 yuborish ==========
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    video_id = call.data
    bot.answer_callback_query(call.id, "Yuklanmoqda... ⏳")

    mp3 = download_mp3(video_id)
    if mp3:
        bot.send_audio(call.message.chat.id, open(mp3, "rb"))
    else:
        bot.send_message(call.message.chat.id, "❌ Yuklab bo‘lmadi.")


# ========== 5) Matn — musiqa qidiruv ==========
@bot.message_handler(func=lambda m: True)
def music_search(msg):
    query = msg.text.strip()
    bot.reply_to(msg, "🔍 Qidirilmoqda...")

    results = search_youtube(query)

    if not results:
        bot.reply_to(msg, "❌ Hech narsa topilmadi.")
        return

    keyboard = telebot.types.InlineKeyboardMarkup()

    for i, (title, vid) in enumerate(results, start=1):
        button = telebot.types.InlineKeyboardButton(
            text=f"{i}. {title[:60]}",
            callback_data=vid
        )
        keyboard.add(button)

    bot.send_message(
        msg.chat.id,
        "🎶 *Topilgan qo‘shiqlar:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# ========== 6) Botni ishga tushirish ==========
bot.infinity_polling()
