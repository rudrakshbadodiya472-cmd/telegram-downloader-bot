import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Simple In-Memory Database for Daily Download Limits
# Structure: {user_id: {"count": int, "date": str}}
user_limits = {}

# 1. Dummy Web Server (To fix Render port binding error)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Start server in a background thread
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
    builder.button(text="💎 Subscribe (₹399)", callback_data="subscribe_menu")
    builder.button(text="🔗 Promote & Earn Link", callback_data="promote_menu")
    builder.button(text="ℹ️ Help", callback_data="help_menu")
    builder.adjust(1)

    await message.answer(
        "👋 **Welcome to Downloader Bot!**\n\nPlease select an option from the menu below:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Callback query handler for download menu
@dp.callback_query(lambda query: query.data == "download_menu")
async def download_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔗 Please send me the link of the video or media you want to download."
    )
    await callback.answer()

# Callback query handler for subscription menu (₹399)
@dp.callback_query(lambda query: query.data == "subscribe_menu")
async def subscribe_menu_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Pay ₹399 Now", url="https://t.me/your_payment_gateway_link")
    builder.button(text="⬅️ Back", callback_data="back_to_home")
    builder.adjust(1)

    await callback.message.edit_text(
        "💎 **Unlock Unlimited Downloads!**\n\n"
        "• Upgrade to Premium for just **₹399**\n"
        "• Remove daily limits (Enjoy unlimited downloads)\n"
        "• High-speed processing\n\n"
        "Click the button below to complete your payment:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Callback query handler for promotion/referral link
@dp.callback_query(lambda query: query.data == "promote_menu")
async def promote_menu_callback(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    referral_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data="back_to_home")
    builder.adjust(1)

    await callback.message.edit_text(
        f"🔗 **Promote & Share Bot**\n\n"
        f"Share your unique promotion link with your friends to invite them to the bot:\n\n"
        f"`{referral_link}`\n\n"
        f"Copy the link above and share it on social media!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Callback query handler for help menu
@dp.callback_query(lambda query: query.data == "help_menu")
async def help_menu_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data="back_to_home")
    builder.adjust(1)

    await callback.message.edit_text(
        "💡 **Help Menu:**\n\n"
        "• Free users get 3 downloads per day.\n"
        "• Upgrade to the ₹399 subscription for unlimited downloads.\n"
        "• Send any supported media link to download it instantly.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Back to home callback
@dp.callback_query(lambda query: query.data == "back_to_home")
async def back_to_home_callback(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Download Video", callback_data="download_menu")
    builder.button(text="💎 Subscribe (₹399)", callback_data="subscribe_menu")
    builder.button(text="🔗 Promote & Earn Link", callback_data="promote_menu")
    builder.button(text="ℹ️ Help", callback_data="help_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        "👋 **Welcome Back!**\n\nPlease select an option from the menu below:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Text message handler for downloading with daily limit check
@dp.message()
async def download_video(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        await message.answer("⚠️ Please send a valid URL link.")
        return

    user_id = message.from_user.id
    import datetime
    today_str = datetime.date.today().isoformat()

    # Initialize or reset daily limit tracking
    if user_id not in user_limits or user_limits[user_id]["date"] != today_str:
        user_limits[user_id] = {"count": 0, "date": today_str}

    # Check if user has exceeded the 3 downloads limit
    if user_limits[user_id]["count"] >= 3:
        builder = InlineKeyboardBuilder()
        builder.button(text="💎 Upgrade for ₹399", callback_data="subscribe_menu")
        await message.answer(
            "⚠️ You have reached your daily limit of 3 free downloads.\n\n"
            "Please upgrade to the ₹399 subscription to enjoy unlimited downloads.",
            reply_markup=builder.as_markup()
        )
        return

    processing_msg = await message.answer("⏳ Downloading video, please wait...")

    output_file = "downloaded_video.mp4"

    # yt-dlp configurations with cookies support to bypass bot checks
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_file,
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    # Automatically add cookies file if present in repository
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_file):
            user_limits[user_id]["count"] += 1
            remaining = 3 - user_limits[user_id]["count"]

            await message.answer_video(
                types.FSInputFile(output_file), 
                caption=f"✅ Here is your video!\n💬 Free downloads remaining today: {remaining}/3"
            )
            os.remove(output_file)
        else:
            await message.answer("❌ Failed to download the video.")
            
    except Exception as e:
        await message.answer(f"❌ An error occurred: {str(e)}")
        
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
        try:
            await processing_msg.delete()
        except:
            pass

async def main():
    print("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
