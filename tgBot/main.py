import asyncio

import numpy as np

import config
import logging

from aiogram import Bot, Dispatcher

from model import MyModel
from config import PATH_TO_MODEL
from handlers import router


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if config.CREATE_DUMMY_MODEL:
        model = MyModel()
        model.fit(np.arange(2), np.arange(2))
        model.dump(PATH_TO_MODEL)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
