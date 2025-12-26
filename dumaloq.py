

import os
import asyncio
import datetime
import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔥 API ma'lumotlarini qo'lda kiritish
API_ID =   # 🔴 API_ID ni Telegramdan oling
API_HASH = '' # 🔴 API_HASH ni Telegramdan oling
BOT_TOKEN = "8068503953:AAEU-3bvxEdQm0BbQbfL4N4bD01Khee5Fmw"  # 🔴 BOT_TOKEN ni BotFather-dan oling

# 🔥 Pyrogram botini yaratish
bot = Client(
    "RoundVideoBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 📂 Foydalanuvchi videolari saqlanadigan papka
SAVE_DIR = "saved_videos"
os.makedirs(SAVE_DIR, exist_ok=True)

# 📌 Bot start bosilganda salomlashish
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    text = ("👋 Assalomu alaykum!\n\n"
            "Bu bot yuborgan videolaringizni yumaloq shaklga keltirib, sifatini oshirib, hajmini kichraytirib beradi! 🎥\n\n"
            "📥 Video yuboring va natijani kuting!")
    
    await message.reply_text(text)

# 📌 Video yuborganda
@bot.on_message(filters.video | filters.document)
async def process_video(client, message: Message):
    video = message.video or message.document
    user = message.from_user

    # 🔔 Foydalanuvchiga xabar berish
    processing_message = await message.reply_text("⏳ Videongiz tayyorlanmoqda...")

    # 📥 Videoni yuklab olish
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    username = user.username if user.username else "NoUsername"
    filename = f"{username}_{user.first_name}_{timestamp}.mp4"
    file_path = os.path.join(SAVE_DIR, filename)
    converted_file = os.path.join(SAVE_DIR, f"converted_{timestamp}.mp4")

    await client.download_media(video, file_path)

    try:
        # 🔍 Video o‘lchamini olish
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
        width, height = int(video_stream["width"]), int(video_stream["height"])

        # 📏 Eng kichik tomonni olish (yumaloq qilish uchun)
        size = min(width, height)

        # 🚀 FFmpeg orqali videoni konvertatsiya qilish
        command = [
            "ffmpeg", "-i", file_path,
            "-vf", f"crop={size}:{size},scale=512:512,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-r", "30",
            "-b:v", "400k",
            "-c:a", "aac",
            "-b:a", "128k",
            converted_file
        ]

        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg xatolik berdi: {stderr.decode()}")

        # 📤 Yumaloq video yuborish
        try:
            await client.send_video_note(
                chat_id=message.chat.id,
                video_note=converted_file
            )
        except Exception as e:
            print(f"❌ Video Note jo‘natishda xatolik: {str(e)}")
            await client.send_video(
                chat_id=message.chat.id,
                video=converted_file
            )

        # ✅ Jarayon tugagani haqida bildirish
        await processing_message.edit("✅ Video tayyor va yuborildi!")

    except Exception as e:
        await processing_message.edit(f"❌ Xatolik yuz berdi: {str(e)}")
        print(f"❌ Xatolik: {str(e)}")

    finally:
        # 🧹 Foydalanilgan fayllarni o‘chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(converted_file):
            os.remove(converted_file)

# 🚀 Botni ishga tushirish
print("✅ Bot ishga tushdi...")
bot.run()

