import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 1. Dummy Web Server (Render ke port error ko fix karne ke liye)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Server ko background thread mein start karna
threading.Thread(target=run_server, daemon=True).start()

# 2. Telegram Bot Setup
TOKEN = "8783060174:AAEYx0XU55aO9QJ9s8pU1hf5nZn4heANuJE"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# /start command handler with options/buttons
@dp.message(Command("start"))
async def start_command(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Download Video", callback_data="download_menu")
    builder.button(text="ℹ️ Help", callback_data="help_menu")
    builder.adjust(1) # Buttons ko ek ke niche ek rakhne ke liye

    await message.answer(
        "👋 **Welcome to Downloader Bot!**\n\nAapko kya karna hai, niche diye gaye options mein se select karein:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Callback query handler for buttons
@dp.callback_query(lambda query: query.data == "download_menu")
async def download_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔗 Kripya mujhe kisi bhi video ya media ka link bhelein jise aap download karna chahte hain."
    )
    await callback.answer()

@dp.callback_query(lambda query: query.data == "help_menu")
async def help_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💡 **Help Menu:**\n\nIs bot ki madad se aap easily links bhej kar videos download kar sakte hain. Bas apna link paste karein!"
    )
    await callback.answer()

# Text message handler (Jab user link ya koi text bhejega)
@dp.message()
async def handle_message(message: types.Message):
    await message.answer(f"Aapne link bheja hai: `{message.text}`\n\nAbhi yahan download processing logic active kar sakte hain!", parse_mode="Markdown")

async def main():
    print("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
