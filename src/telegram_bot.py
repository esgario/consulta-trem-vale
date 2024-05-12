import dotenv
import telegram

config = dotenv.dotenv_values("src/.env")

bot = telegram.Bot(token=config["TELEGRAM_BOT_TOKEN"])
chat_id = config["TELEGRAM_CHAT_ID"]

async def send_message(text):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)


