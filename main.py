import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
from aiogram import Bot, Dispatcher, types

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

# /start command handler
@dp.message(lambda message: message.text == "/start")
async def start_command(message: types.Message):
    await message.answer("Hello! Mera downloader bot ab live aur ready hai.")

async def main():
    print("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
