import os
import sqlite3
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp
from flask import Flask
from threading import Thread

# --- RENDER ÜÇÜN DAXİLİ SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "TikTok.az Bot Aktivdir!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- KONFİQURASİYA ---
API_TOKEN = '8372958619:AAEvHAS5aKilEh9xkk4dotSD5n92s0v7AbA'
ADMIN_ID = 8446711093
LOGO_PATH = "image_02dbe1.jpg"

ZARAFATLAR = [
    "🛸 Video yoldadır, tıxaca düşüb...",
    "🤖 Botumuz qonşunun Wi-Fi-ına bağlanmağa çalışır...",
    "🚀 Videonu loqosuz çıxarmaq üçün TikTok-un qapısını qırıram!",
    "🧐 Yüklənir... Bu arada, bu gün çox yaraşıqlı görünürsən!",
    "🧗‍♂️ Serverimiz videonu yükləmək üçün dağları aşır..."
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MƏLUMAT BAZASI (Render üçün optimallaşdırılmış) ---
try:
    # Render-də fayl yazmaq icazəsi üçün /tmp/ istifadə edirik
    DB_PATH = "/tmp/tiktok_az.db"
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
except Exception as e:
    logging.error(f"Baza yaradılarkən xəta: {e}")

def save_user(user_id):
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except Exception as e:
        # Baza işləməsə belə log yaz, amma botun işini dayandırma
        logging.error(f"İstifadəçi qeyd edilə bilmədi: {e}")

# --- YÜKLƏMƏ FUNKSİYASI ---
def download_media(url):
    output_file = 'downloaded_video.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_file,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_file

# --- ANA MENYU ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Rəsmi Kanal", url="https://t.me/azernews_az"))
    builder.row(
        InlineKeyboardButton(text="⭐ Bizi Qiymətləndir", callback_data="rate"),
        InlineKeyboardButton(text="👨‍💻 Dəstək", url=f"tg://user?id={ADMIN_ID}")
    )
    return builder.as_markup()

# --- KOMANDALAR ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # İstifadəçini yadda saxla (xəta olsa belə start mesajını göndər)
    save_user(message.from_user.id)
    caption = (
        f"👋 **Salam, {message.from_user.first_name}!**\n\n"
        "🔥 **TikTok.az** botuna xoş gəlmisən!\n"
        "Mən **TikTok** və **Instagram** videolarını loqosuz yükləyirəm.\n\n"
        "📥 **Yükləmək üçün linki göndərin:**"
    )
    if os.path.exists(LOGO_PATH):
        await message.answer_photo(photo=FSInputFile(LOGO_PATH), caption=caption, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await message.answer(caption, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "rate")
async def process_rate(callback: CallbackQuery):
    await callback.answer("Təşəkkür edirik! ⭐⭐⭐⭐⭐", show_alert=True)
    await callback.message.answer("🌟 **Dəstəyiniz üçün minnətdarıq!**", parse_mode="Markdown")

@dp.message(Command("reklam"))
async def cmd_reklam(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("📝 Reklam mətni yazın.")
    
    try:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        count = 0
        for user in users:
            try:
                await bot.send_message(user[0], f"📢 **TikTok.az Elanı**\n\n{args[1]}", parse_mode="Markdown")
                count += 1
                await asyncio.sleep(0.05)
            except:
                continue
        await message.answer(f"✅ Reklam {count} nəfərə çatdırıldı.")
    except Exception as e:
        await message.reply(f"❌ Reklam göndərilərkən baza xətası: {e}")

# --- VİDEO YÜKLƏMƏ PROSESİ (HƏR KƏS ÜÇÜN) ---
@dp.message(F.text.contains("tiktok.com") | F.text.contains("instagram.com"))
async def handle_media(message: types.Message):
    # İstənilən istifadəçini bazaya əlavə etməyə çalış
    save_user(message.from_user.id)
    
    platform = "Instagram" if "instagram.com" in message.text else "TikTok"
    zarafat = random.choice(ZARAFATLAR)
    status = await message.answer(f"🚀 **{platform} bağlantısı qurulur...**\n\n_{zarafat}_", parse_mode="Markdown")
    
    try:
        await status.edit_text(f"📥 **Video loqosuz çəkilir...**\n\n_{zarafat}_", parse_mode="Markdown")
        path = await asyncio.to_thread(download_media, message.text)
        
        await status.edit_text("📤 **Hazırdır! Göndərilir...**")
        video_file = FSInputFile(path)
        
        await message.answer_video(video_file, caption=f"✅ **{platform} yükləndi!**\n🚀 admin: @umudhasanovtm", reply_markup=main_menu())
        
        if os.path.exists(path):
            os.remove(path)
        await status.delete()
    except Exception as e:
        await status.edit_text("❌ **Xəta!** Linki yoxlayın və ya profilin açıq olduğundan əmin olun.")
        logging.error(f"Error: {e}")

async def main():
    Thread(target=run_web).start()
    print("TikTok.az Bot Aktivdir!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

