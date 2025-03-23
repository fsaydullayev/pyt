import asyncio
import nest_asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime, time
import pytz  # Vaqt zonasini aniqlash uchun

# nest_asyncio ni qo‘llash
nest_asyncio.apply()

# Bot tokenini shu yerga kiriting
BOT_TOKEN = "7539341376:AAEsMxfCsRVMNGuE78NZ4KJwXenQy0ZXRy8"

# JSON fayl yo'li
DATA_FILE = "birthdays.json"

# O‘zbekiston vaqtini olish
UZBEKISTAN_TZ = pytz.timezone("Asia/Tashkent")

# Ma'lumotlarni yuklash va saqlash funksiyalari
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

data = load_data()

def calculate_age(birth_date):
    today = datetime.now(UZBEKISTAN_TZ).date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

async def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"Assalamu alaykum, {user_name}! 😊\n"
        "Men tug'ilgan kuningizga qancha qolganini va hozirgi yoshingizni aniqlab beraman.\n"
        "Tug'ilgan kuningizni **KUN OY YIL** formatida yozing. Masalan: `20 12 1999`"
    )

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    user_name = update.message.from_user.first_name
    username = update.message.from_user.username if update.message.from_user.username else "No username"
    message_text = update.message.text

    try:
        birth_date = datetime.strptime(message_text, "%d %m %Y").date()
        
        data[user_id] = {
            "birth_date": birth_date.strftime("%Y-%m-%d"),
            "first_name": user_name,
            "username": username
        }
        save_data(data)

        today = datetime.now(UZBEKISTAN_TZ).date()

        if birth_date.day == today.day and birth_date.month == today.month:
            await update.message.reply_text(
                f"🎂🎉 {user_name}!\n"
                "VOOOY 🤩 Bugun sizning tug'ilgan kuningiz! 🎈\n"
                "Tavalludingiz bilan tabriklayman! 🥳\n"
                "Hurmat bilan @F_Saydullayev 💫"
            )
        else:
            next_birthday = birth_date.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)

            days_left = (next_birthday - today).days
            age = calculate_age(birth_date)

            await update.message.reply_text(
                f"{user_name}, tug'ilgan kuningizga {days_left} kun qoldi! 🎉\n"
                f"Sizning yoshingiz: {age} yosh ⚡"
            )

        print(f"📢 Foydalanuvchi: {user_name} (@{username})")
        print(f"📅 Tug'ilgan sana: {message_text}")
        print("-" * 40)
    
    except ValueError:
        await update.message.reply_text("Iltimos, tug'ilgan kuningizni **KUN OY YIL** formatida yozing. Masalan: `10 04 2005`")

async def send_daily_updates(context: CallbackContext):
    today = datetime.now(UZBEKISTAN_TZ).date()
    
    for user_id, user_info in list(data.items()):
        try:
            birth_date_str = user_info.get("birth_date")
            if not birth_date_str:
                continue

            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            next_birthday = birth_date.replace(year=today.year)

            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)

            days_left = (next_birthday - today).days

            if days_left == 0:
                message = (
                    f"🎂🎉 {user_info['first_name']}!\n"
                    "VOOOY 🤩 Bugun sizning tug'ilgan kuningiz ekan! 🎈\n"
                    "Tavalludingiz bilan tabriklayman!Ishlaringizga rivoj umrizga baraka tilayman 🥳\n"
                    "Hurmat bilan @F_Saydullayev 💫"
                )
            else:
                message = f"{user_info['first_name']}, tug'ilgan kuningizga {days_left} kun qoldi! 🗓"

            await context.bot.send_message(chat_id=user_id, text=message)
            print(f"📢 Eslatma yuborildi: {user_info['first_name']} (@{user_info.get('username', 'No username')})")
            print(f"📅 Tug‘ilgan sana: {birth_date_str} | 🗓 Qolgan kun: {days_left}")
            print("-" * 40)

        except Exception as e:
            print(f"❌ Xatolik {user_id} uchun: {e}")

async def schedule_daily_reminders(application: Application):
    """Barcha foydalanuvchilar uchun kunlik eslatmalarni rejalashtirish"""
    application.job_queue.run_daily(send_daily_updates, time=time(21, 18, tzinfo=UZBEKISTAN_TZ))

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bot ishga tushganda kunlik eslatmalarni rejalashtirish
    await schedule_daily_reminders(app)

    print("Bot ishga tushdi...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
