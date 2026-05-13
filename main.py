import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv
from aiohttp import web

# ======================
# ENV
# ======================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ======================
# BOT
# ======================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ======================
# MEMORY
# ======================

posts = {}
user_modes = {}

# ======================
# WEB (Render port)
# ======================

async def handle(request):
    return web.Response(text="Bot is running")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ======================
# NEW POST
# ======================

@dp.message()
async def new_post(message: Message):

    post_id = len(posts) + 1

    posts[post_id] = {
        "text": message.caption or message.text,
        "photo": message.photo[-1].file_id if message.photo else None,
        "video": message.video.file_id if message.video else None,
        "user_id": message.from_user.id,
        "username": message.from_user.username
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🕶 Анонимно", callback_data=f"anon_{post_id}"),
                InlineKeyboardButton(text="👤 С подписью", callback_data=f"author_{post_id}")
            ]
        ]
    )

    await message.answer("Выберите формат публикации 👇", reply_markup=keyboard)

# ======================
# MODE: ANON
# ======================

@dp.callback_query(F.data.startswith("anon_"))
async def anon(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])
    user_modes[post_id] = "anon"

    await send_to_admin(callback, post_id)

# ======================
# MODE: AUTHOR
# ======================

@dp.callback_query(F.data.startswith("author_"))
async def author(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])
    user_modes[post_id] = "author"

    await send_to_admin(callback, post_id)

# ======================
# SEND TO ADMIN
# ======================

async def send_to_admin(callback: CallbackQuery, post_id: int):

    post = posts.get(post_id)
    mode = user_modes.get(post_id, "anon")

    text = post["text"] or "Без текста"

    if mode == "author" and post.get("username"):
        text += f"\n\n👤 Автор: @{post['username']}"
    else:
        text += "\n\n🕶 Анонимно"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"approve_{post_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{post_id}")
            ]
        ]
    )

    if post["photo"]:
        await bot.send_photo(ADMIN_ID, post["photo"], caption=text, reply_markup=keyboard)

    elif post["video"]:
        await bot.send_video(ADMIN_ID, post["video"], caption=text, reply_markup=keyboard)

    else:
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)

    await callback.message.edit_text("⏳ Отправлено на модерацию")

# ======================
# APPROVE
# ======================

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])

    post = posts.get(post_id)
    mode = user_modes.get(post_id, "anon")

    if not post:
        return

    text = post["text"] or ""

    if mode == "author" and post.get("username"):
        text += f"\n\n👤 Автор: @{post['username']}"

    if post["photo"]:
        await bot.send_photo(CHANNEL_ID, post["photo"], caption=text)

    elif post["video"]:
        await bot.send_video(CHANNEL_ID, post["video"], caption=text)

    else:
        await bot.send_message(CHANNEL_ID, text)

    await callback.message.edit_text("✅ Опубликовано")

# ======================
# REJECT
# ======================

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):

    await callback.message.edit_text("❌ Отклонено")

# ======================
# MAIN
# ======================

async def main():

    print("🚀 BOT STARTED")

    await start_web()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
