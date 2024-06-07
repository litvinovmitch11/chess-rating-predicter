import asyncio

import config
import logging

from aiogram import Bot, Dispatcher

from tgBot.model.rating_predictor_model import RatingPredictorModel
from config import PATH_TO_MODEL
from handlers import router


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if config.CREATE_MODEL:
        model = RatingPredictorModel()
        model.fit()
        model.dump(PATH_TO_MODEL)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
