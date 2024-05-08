# Основа бота
import routers
from key import key
from aiogram import Bot, Dispatcher
from routers import router
import asyncio


async def main():
    bot = Bot(token=key)
    dp = Dispatcher()
    dp.include_router(router)
    await routers.create_table()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


