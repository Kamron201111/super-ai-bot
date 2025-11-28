import os
import telebot
import requests
import PyPDF2
from tinydb import TinyDB, Query

# TOKEN GitHub Secrets dan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# Database
db = TinyDB("users.json")
User = Query()

def add_user(uid, ref=None):
    if not db.contains(User.id == uid):
        db.insert({"id": uid, "coins": 0})
        if ref:
            old = db.get(User.id == ref)["coins"]
            db.update({"coins": old + 20}, User.id == ref)

def get_coins(uid):
    u = db.get(User.id == uid)
    return u["coins"]

# ===== AI CHAT =====
def ai_chat(prompt):
    url = "https://api.azzouz.cloud/api/v1/chat/completions"
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "O'zbekcha aqlli AI yordamchi bo'l."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        r = requests.post(url, json=data).json()
        return r["choices"][0]["message"]["content"]
    except:
        return "AI xizmatida xato."

# ===== WEB SEARCH =====
def web_search(query):
    try:
        r = requests.get(f"https://ddg-api.herokuapp.com/search?query={query}").json()
        text = "\n".join([x["snippet"] for x in r["results"][:5]])
        return ai_chat(f"Quyidagi matndan o‘zbekcha xulosa yoz:\n{text}")
    except:
        return None

# ===== STT =====
def stt(file_url):
    audio = requests.get(file_url).content
    open("v.ogg", "wb").write(audio)

    r = requests.post("https://api.groqify.cloud/stt",
                      files={"file": ("v.ogg", open("v.ogg", "rb"))}).json()

    return r.get("text", "Ovoz tanilmadi.")

# ===== TTS =====
def tts(text):
    r = requests.post("https://api.groqify.cloud/tts", json={"text": text})
    open("tts.mp3", "wb").write(r.content)
    return "tts.mp3"

# ===== IMAGE GEN =====
def gen_image(prompt):
    img = requests.get("https://image.pollinations.ai/prompt/" + prompt).content
    open("ai.png", "wb").write(img)
    return "ai.png"

# ===== PDF READER =====
def pdf_reader(path):
    try:
        reader = PyPDF2.PdfReader(path)
        text = "".join([pg.extract_text() for pg in reader.pages])
        return ai_chat(f"PDF dan xulosa yoz:\n{text}")
    except:
        return "PDF o‘qib bo‘lmadi."

# ===== GAME =====
import random
def game():
    return f"🎮 Sizga tushgan son: {random.randint(1,10)}"

# ===== ROUTER =====
def process(text, uid):
    t = text.lower()

    if t.startswith("ref:"):
        add_user(uid, t[4:])
        return f"Referal qabul qilindi! Balans: {get_coins(uid)}"

    if t.startswith("say "):
        file = tts(t[4:])
        return ("file", file)

    if t.startswith("gen "):
        file = gen_image(t[4:])
        return ("file", file)

    if t == "game":
        return game()

    if t.endswith(".pdf"):
        return pdf_reader(t)

    res = web_search(text)
    if res:
        return f"🌍 Internetdan topdim:\n{res}"

    return ai_chat(text)

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    add_user(uid)
    bot.reply_to(msg,
        "👋 Super AI Botga xush kelibsiz!\n"
        "🧠 AI Chat\n🌍 Web qidiruv\n🎙 Ovoz → matn\n🗣 Matn → ovoz\n"
        "🖼 Rasm generatsiya\n📚 PDF o'qish\n🎮 Mini o‘yin\n👤 Referal\n")

# ===== VOICE =====
@bot.message_handler(content_types=['voice'])
def voice(msg):
    file = bot.get_file(msg.voice.file_id)
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    txt = stt(url)
    bot.reply_to(msg, f"🎙 Ovoz matnga:\n{txt}")

# ===== TEXT =====
@bot.message_handler(func=lambda m: True)
def txt(msg):
    res = process(msg.text, msg.from_user.id)

    if isinstance(res, tuple):
        if res[0] == "file":
            bot.send_document(msg.chat.id, open(res[1], "rb"))
    else:
        bot.reply_to(msg, res)

bot.infinity_polling()
