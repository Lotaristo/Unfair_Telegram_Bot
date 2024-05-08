# Основной рабочий файл

from aiogram.filters import Command, CommandStart
from aiogram.types import  CallbackQuery, Message
from aiogram import  F, Router

import aiosqlite

import keyboard as kb
from quiz_data import quiz_data

router = Router()
DB_NAME = 'quiz_bot.db'
is_correct = 0

#Запуск бота
@router.message(CommandStart())
async def start(message: Message):
    await message.answer(f'Привет, {message.from_user.first_name}. Нажми на кнопку, чтобы начать игру, или напиши "quiz".\nДля просмотра статистики по всем игрокам, используй команду "/info"', reply_markup=kb.start_game())


# Начало игры
@router.message(F.text == "Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    await message.answer(f"Привет, игрок! Сегодня у тебя есть уникальная возможность сыграть в небольшую игру и правильно ответить на 10 вопросов. Только не ожидай, что игра будет честной, а ответы очевидными. Удачи!")
    await new_quiz(message)

# Получение статистики по игрокам
@router.message(Command('info'))
async def show_info(message: Message):
    info = await get_info()
    text = ''
    for row in info:
        text += f'ID игрока: {row[0]}, Количество баллов: {row[1]}\n'
    await message.answer(f'Статистика по игрокам:\n{text}')


# Выбор ответа
@router.callback_query(lambda x: x.data in ["right_answer", "wrong_answer"])
async def get_answer(callback: CallbackQuery):
    global is_correct
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None)

    if callback.data == "right_answer":
        await callback.message.answer("Поздравляю, ты угадал!")
        is_correct += 1
        print(is_correct)
    else:
        await callback.message.answer("Увы, но нет!")
        print(is_correct)

    current_question_index = await get_quiz_index(callback.from_user.id)

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await add_correct_answers(callback.from_user.id, is_correct)
        await callback.message.answer(f"Это был последний вопрос. Поздравляю с окончанием! Надеюсь, тебе понравилось :)\nТвой итоговый счет: {is_correct} баллов")


# Обновление таблицы
async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)

    await get_question(message, user_id)


# Вопрос
async def get_question(message, user_id):
    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']

    kb_options = kb.generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb_options)


#Получение данных из таблицы
async def get_quiz_index(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


#Обновление таблицы
async def update_quiz_index(user_id, index):
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR IGNORE INTO quiz_state (user_id) VALUES (?)', (user_id,))
        await db.execute('UPDATE quiz_state SET correct_answers = correct_answers + ?, question_index = ? WHERE user_id = ?',
            (is_correct, index, user_id))
        await db.commit()


#Создание таблицы
async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
                                                                    user_id INTEGER PRIMARY KEY,
                                                                    question_index INTEGER,
                                                                    correct_answers INTEGER DEFAULT 0)''')
        await db.commit()


# Добавление статистики в таблицу
async def add_correct_answers(user_id, is_correct):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO quiz_state (user_id) VALUES (?)', (user_id,))
        await db.execute('UPDATE quiz_state SET correct_answers = ? WHERE user_id = ?', (is_correct, user_id))
        await db.commit()


#Получение статистики из таблицы
async def get_info():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, correct_answers FROM quiz_state') as cursor:
            results = await cursor.fetchall()
            return results












