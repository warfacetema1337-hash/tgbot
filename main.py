import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

posts = {}

# ---------------- BOT ----------------

@dp.message()
async def new_post(message: Message):
    post_id = len(posts) + 1
    posts[post_id] = message.text

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"yes_{post_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{post_id}")
            ]
        ]
    )

    await bot.send_message(
        ADMIN_ID,
        f"📩 Новая предложка:\n\n{message.text}",
        reply_markup=kb
    )

    await message.answer("Отправлено на модерацию 👍")


@dp.callback_query(F.data.startswith("yes_"))
async def approve(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[1])
    text = posts.get(post_id)

    if text:
        await bot.send_message(CHANNEL_ID, text)
        await callback.message.edit_text(f"✅ Опубликовано:\n\n{text}")


@dp.callback_query(F.data.startswith("no_"))
async def reject(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[1])
    text = posts.get(post_id)

    if text:
        await callback.message.edit_text(f"❌ Отклонено:\n\n{text}")

# ---------------- WEB SERVER (для Render) ----------------

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

# ---------------- MAIN ----------------

async def main():
    print("BOT STARTED")

    await start_web()      # ← ВАЖНО: даём Render порт
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())