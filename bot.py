import logging
import os
import requests
import aiohttp
import PyPDF2
from tinydb import TinyDB, Query
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token GitHub Secrets dan olinadi

db = TinyDB("users.json")
User = Query()

def add_user(uid, ref=None):
    if not db.contains(User.id == uid):
        db.insert({"id": uid, "coins": 0})
        if ref:
            db.update({"coins": db.get(User.id == ref)["coins"] + 20}, User.id == ref)

def get_coins(uid):
    u = db.get(User.id == uid)
    return u.get("coins", 0)

async def ai_chat(prompt):
    url = "https://api.azzouz.cloud/api/v1/chat/completions"
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Sen o'zbekcha gapiradigan kuchli AI yordamchisan."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, json=data) as r:
                j = await r.json()
                return j["choices"][0]["message"]["content"]
    except:
        return "❌ AI serveri ishlamadi."

async def web_search(query):
    try:
        data = requests.get(f"https://ddg-api.herokuapp.com/search?query={query}").json()
        text = "\n".join([x["snippet"] for x in data["results"][:5]])
        return await ai_chat(f"Quyidagi ma‘lumotlardan o‘zbekcha xulosa chiqar:\n{text}")
    except:
        return None

async def process_query(q):
    keys = ["kim", "qayer", "qachon", "qancha", "yangilik", "news", "ma'lumot"]
    if any(k in q.lower() for k in keys):
        r = await web_search(q)
        if r:
            return f"🌍 Internetdan topdim:\n\n{r}"
    return await ai_chat(q)

async def voice_to_text(url):
    content = requests.get(url).content
    open("voice.ogg", "wb").write(content)
    r = requests.post("https://api.groqify.cloud/stt",
                      files={"file": ("voice.ogg", open("voice.ogg", "rb"))})
    return r.json().get("text", "❌ Ovozni ajratib bo‘lmadi.")

async def text_to_voice(t):
    r = requests.post("https://api.groqify.cloud/tts", json={"text": t})
    open("tts.mp3", "wb").write(r.content)
    return "tts.mp3"

async def generate_image(prompt):
    img = requests.get("https://image.pollinations.ai/prompt/" + prompt).content
    open("ai.png", "wb").write(img)
    return "ai.png"

async def pdf_reader(path):
    try:
        pdf = PyPDF2.PdfReader(path)
        text = "".join([p.extract_text() for p in pdf.pages])
        return await ai_chat(f"PDF matnidan xulosa chiqaring:\n{text}")
    except:
        return "❌ PDF o‘qishda xatolik."

async def random_game():
    import random
    return f"🎮 Sizga tushgan son: {random.randint(1,10)}"

async def router(text, update, context):
    if text.startswith("ref:"):
        ref = text.replace("ref:", "").strip()
        add_user(update.effective_user.id, ref)
        return f"Referal qabul qilindi! Balansingiz: {get_coins(update.effective_user.id)}"

    if text.startswith("say "):
        v = await text_to_voice(text[4:])
        return InputFile(v)

    if text.startswith("gen "):
        i = await generate_image(text[4:])
        return InputFile(i)

    if text == "game":
        return await random_game()

    if text.endswith(".pdf"):
        return await pdf_reader(text)

    return await process_query(text)

async def handler(update, context):
    if update.message.voice:
        file = await context.bot.get_file(update.message.voice.file_id)
        t = await voice_to_text(file.file_path)
        return await update.message.reply_text(f"🎙 Ovoz matnga:\n\n{t}")

    if update.message.text:
        t = update.message.text
        await update.message.reply_text("⏳ Qayta ishlayapman...")
        result = await router(t, update, context)

        if isinstance(result, InputFile):
            return await update.message.reply_document(result)
        return await update.message.reply_text(result)

async def start(update, context):
    u = update.effective_user
    add_user(u.id)
    ref = f"https://t.me/{context.bot.username}?start={u.id}"

    await update.message.reply_text(
        "👋 SUPER MEGA BOTGA XUSH KELDINGIZ!\n"
        "🧠 AI Chat\n🌍 Internet qidiruv\n🎙 Ovoz → Matn\n🗣 Matn → Ovoz\n"
        "🖼 Surat generatsiya\n📚 PDF o‘qish\n🎮 Mini o‘yin\n👤 Referal\n\n"
        f"Referal: {ref}"
    )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handler))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
