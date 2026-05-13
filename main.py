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

# =========================
# LOAD ENV
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# =========================
# BOT
# =========================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# =========================
# STORAGE
# =========================

posts = {}
user_modes = {}

# =========================
# WEB SERVER FOR RENDER
# =========================

async def handle(request):
    return web.Response(text="Bot is running")

async def start_webserver():

    app = web.Application()

    app.router.add_get("/", handle)

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

# =========================
# NEW POST
# =========================

@dp.message(F.text | F.photo | F.video)
async def new_post(message: Message):

    post_id = len(posts) + 1

    posts[post_id] = {
        "text": message.caption or message.text,
        "photo": message.photo[-1].file_id if message.photo else None,
        "video": message.video.file_id if message.video else None,
        "username": message.from_user.username
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🕶 Анонимно",
                    callback_data=f"anon_{post_id}"
                ),
                InlineKeyboardButton(
                    text="👤 С подписью",
                    callback_data=f"author_{post_id}"
                )
            ]
        ]
    )

    await message.answer(
        "📩 Предложка получена!\n\nВыберите формат публикации:",
        reply_markup=keyboard
    )

# =========================
# ANON
# =========================

@dp.callback_query(F.data.startswith("anon_"))
async def anon(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])

    user_modes[post_id] = "anon"

    await send_to_admin(callback, post_id)

# =========================
# AUTHOR
# =========================

@dp.callback_query(F.data.startswith("author_"))
async def author(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])

    user_modes[post_id] = "author"

    await send_to_admin(callback, post_id)

# =========================
# SEND TO ADMIN
# =========================

async def send_to_admin(callback: CallbackQuery, post_id: int):

    post = posts.get(post_id)

    if not post:
        return

    mode = user_modes.get(post_id)

    text = post["text"] or "Без текста"

    if mode == "author":

        if post["username"]:
            text += f"\n\n👤 Автор: @{post['username']}"
        else:
            text += "\n\n👤 Автор без username"

    else:
        text += "\n\n🕶 Анонимно"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data=f"approve_{post_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{post_id}"
                )
            ]
        ]
    )

    # PHOTO
    if post["photo"]:

        await bot.send_photo(
            ADMIN_ID,
            post["photo"],
            caption=f"📩 <b>Новая предложка</b>\n\n{text}",
            reply_markup=keyboard
        )

    # VIDEO
    elif post["video"]:

        await bot.send_video(
            ADMIN_ID,
            post["video"],
            caption=f"📩 <b>Новая предложка</b>\n\n{text}",
            reply_markup=keyboard
        )

    # TEXT
    else:

        await bot.send_message(
            ADMIN_ID,
            f"📩 <b>Новая предложка</b>\n\n{text}",
            reply_markup=keyboard
        )

    await callback.message.edit_text(
        "✅ Отправлено на модерацию"
    )

# =========================
# APPROVE
# =========================

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):

    post_id = int(callback.data.split("_")[1])

    post = posts.get(post_id)

    if not post:
        return

    mode = user_modes.get(post_id)

    text = post["text"] or ""

    if mode == "author":

        if post["username"]:
            text += f"\n\n👤 Автор: @{post['username']}"

    # PHOTO
    if post["photo"]:

        await bot.send_photo(
            CHANNEL_ID,
            photo=post["photo"],
            caption=text
        )

    # VIDEO
    elif post["video"]:

        await bot.send_video(
            CHANNEL_ID,
            video=post["video"],
            caption=text
        )

    # TEXT
    else:

        await bot.send_message(
            CHANNEL_ID,
            text
        )

    try:
        await callback.message.edit_caption(
            caption="✅ Опубликовано"
        )
    except:
        await callback.message.edit_text(
            "✅ Опубликовано"
        )

# =========================
# REJECT
# =========================

@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):

    try:
        await callback.message.edit_caption(
            caption="❌ Отклонено"
        )
    except:
        await callback.message.edit_text(
            "❌ Отклонено"
        )

# =========================
# MAIN
# =========================

async def main():

    print("🚀 BOT STARTED")

    await start_webserver()

    await dp.start_polling(bot)

# =========================
# START
# =========================

if __name__ == "__main__":
    asyncio.run(main())
