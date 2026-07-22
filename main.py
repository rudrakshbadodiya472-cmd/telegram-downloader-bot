import asyncio
import logging
import os
import tempfile
import yt_dlp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

# Logging configuration
logging.basicConfig(level=logging.INFO)

# TODO: Apna BotFather se mila verified token yahan dalein
API_TOKEN = "8783060174:AAEYx0XU55aO9QJ9s8pU1hf5nZn4heANuJE"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ----------------- IN-MEMORY DATABASES -----------------
user_downloads = {}      
user_affiliates = {}     
affiliate_earnings = {}  
DAILY_LIMIT = 3


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) > 1 and args[1].startswith("ref_"):
        aff_id = args[1].replace("ref_", "")
        if user_id not in user_affiliates and str(user_id) != aff_id:
            user_affiliates[user_id] = aff_id
            affiliate_earnings[aff_id] = affiliate_earnings.get(aff_id, 0) + 1

    welcome_text = (
        "👋 **Welcome to Pro Media Downloader Bot!**\n\n"
        "Send me any Instagram Reel, YouTube Short, or video link to get a clean, watermark-free download.\n\n"
        f"🎁 Free Tier: {DAILY_LIMIT} downloads today.\n"
        "💎 Get Unlimited Access: /upgrade\n"
        "🤝 Earn Money by Promoting: /affiliate"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message(Command("upgrade"))
async def cmd_upgrade(message: types.Message):
    upgrade_text = (
        "🚀 **Unlock Pro Access (₹299/month)**\n\n"
        "• Unlimited high-speed downloads\n"
        "• No watermarks & Bulk processing\n"
        "• Priority servers\n\n"
        "👉 **Pay securely via UPI / Razorpay:**\n"
        "https://rzp.io/l/your-payment-gateway-link"
    )
    await message.answer(upgrade_text, parse_mode="Markdown")


@dp.message(Command("affiliate"))
async def cmd_affiliate(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    referrals_count = affiliate_earnings.get(str(user_id), 0)

    affiliate_text = (
        "🤝 **Affiliate Partner Program**\n\n"
        "Earn 40% commission on every user who upgrades to Pro through your link!\n\n"
        f"🔗 **Your Unique Referral Link:**\n`{ref_link}`\n\n"
        f"📊 **Total Users Referred:** {referrals_count}\n"
        "💰 **Estimated Earnings:** ₹" + str(referrals_count * 120) + "\n\n"
        "Share this link in Telegram groups, status, or with friends to start earning!"
    )
    await message.answer(affiliate_text, parse_mode="Markdown")


@dp.message(F.text.startswith("http"))
async def handle_media_link(message: types.Message):
    user_id = message.from_user.id
    url = message.text.strip()

    current_count = user_downloads.get(user_id, 0)
    if current_count >= DAILY_LIMIT:
        await message.answer(
            "⚠️ Aapki aaj ki free limit khatam ho chuki hai!\n"
            "Unlimited downloads ke liye /upgrade command ka use karein."
        )
        return

    processing_msg = await message.answer("⏳ Downloading video, please wait...")

    temp_dir = tempfile.gettempdir()
    output_template = os.path.join(temp_dir, f"{user_id}_%(id)s.%(ext)s")

    filename = None
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'max_filesize': 50 * 1024 * 1024,  # 50MB limit for telegram
            'socket_timeout': 15,
            'quiet': True
        }

        # Run yt-dlp in a thread to keep async event loop non-blocked
        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        loop = asyncio.get_running_loop()
        filename = await loop.run_in_executor(None, download_media)

        user_downloads[user_id] = current_count + 1
        remaining = DAILY_LIMIT - user_downloads[user_id]

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass

        video_file = FSInputFile(filename)
        await message.answer_video(
            video=video_file,
            caption=f"✅ **Watermark-Free Download Ready!**\n📊 Remaining free downloads today: {remaining}",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass
        await message.answer("❌ Media fetch karne mein samasya aayi. Kripya valid public link bhejein.")

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass


async def main():
    print("Bot is starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())