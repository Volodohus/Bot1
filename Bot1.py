import asyncio
import logging
import sqlite3
from aiogram.client import bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton
from aiogram import F
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Filter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from test import toki

# ДЗ: сделать бота, который будет запрашивать данные пользователя и сохранять их в стейт.
# Со звездочкой: так же сохранять и в базу данных.

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot1 = bot.Bot(token= toki)
dp = Dispatcher()

baza = sqlite3.connect('bazuka.db')
buz = baza.cursor()

buz.execute('''CREATE TABLE IF NOT EXISTS Units (id INTEGER PRIMARY KEY, Name TEXT, Surname TEXT, Age TEXT)''')


@dp.message(Command( "start"))
async def cmd_start(message: types.Message):
    await  message.answer("Добренького. Справка по командам /help")

@dp.message(Command( "help"))
async def cmd_help(message: types.Message):
    await  message.answer('"/ab" - Добавить себя в базу\n '
                          '"/db" - удалить себя из базы\n '
                          '"/ib" - посмотреть информацию в базе')


@dp.message(F.text == "s")
async def cmd_start2(mes: types.Message):
    bt = InlineKeyboardButton(text='t',callback_data='s')
    pol = InlineKeyboardMarkup(inline_keyboard=[
        [bt,bt]
    ])
    await mes.answer(text='t',reply_markup = pol)

class Sb(StatesGroup):
    userID  = State()
    name    = State()
    fam     = State()
    voz     = State()
    da      = State()

@dp.message(Command('ab'))
async def bID(mes: Message, state: FSMContext) -> None:
    await state.update_data(userID = mes.from_user.id)
    dat = await state.get_data()
    await state.set_state(Sb.name)
    await mes.answer(text=f"Я, звать - Разорвать, Фамилия - Лопнуть\nЗвать тебя как?")
    logging.info("KUKU",  [dat])

@dp.message(Sb.name)
async  def bN(mes: Message, state: FSMContext) -> None:
    await state.update_data(name=mes.text)
    dat = await state.get_data()
    logging.info("KUKU", [dat])
    await state.set_state(Sb.fam)
    await mes.answer('Лопнул шарик, виновен:')

@dp.message(Sb.fam)
async  def bN(mes: Message, state: FSMContext) -> None:
    await state.update_data(fam=mes.text)
    dat = await state.get_data()
    logging.info("KUKU", [dat])
    await state.set_state(Sb.voz)
    await mes.answer('Сколько раз надували ширики для тебя:')

@dp.message(Sb.voz)
async  def bN(mes: Message, state: FSMContext) -> None:
    await state.update_data(voz=mes.text)
    dat = await state.get_data()
    us = mes.from_user
    logging.info("KUKU", [dat,us])
    await mes.answer(text =f'Ты {dat["fam"]} {dat["name"]} возраст:{dat["voz"]}.\nДобавить тебя в базу?',reply_markup=ReplyKeyboardMarkup(keyboard =[[KeyboardButton(text='Да'),KeyboardButton(text='Нет')]]))
    await state.set_state(Sb.da)

@dp.message(Sb.da)
async def danu(mes: Message, state: FSMContext) -> None:
    if mes.text.lower() == "да":
        dat = await state.get_data()
        logging.info("KUKU", [dat])

        buz.execute(f'''SELECT id from Units where id = {dat['userID']}''')
        sq = buz.fetchall()

        if (dat['userID']) in sq:
            buz.execute(f'''UPDATE Units SET Name = ?, Surname=?, Age=? WHERE id = {dat['userID']}''',(dat['name'],dat['fam'],dat['voz']))
            await mes.answer(text='Твои данные изменены.', reply_markup=ReplyKeyboardRemove())

        elif (dat['userID']) not in sq:
            buz.execute('''INSERT INTO Units (id,Name,Surname,Age) VALUES (?,?,?,?)''',(dat['userID'],dat['name'],dat['fam'],dat['voz']))
            await mes.answer(text='Добро пожаловать.', reply_markup=ReplyKeyboardRemove())
        else:
            await mes.answer(text='хня', reply_markup=ReplyKeyboardRemove())
        baza.commit()
        await state.clear()
    elif mes.text.lower() == 'нет':
        await mes.answer(text='Лучше бы добавиться.',reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:

        await mes.answer(text='Нет так нет. Чего выпендриваешься?!',reply_markup=ReplyKeyboardRemove())
        await state.clear()

@dp.message(Command('ib'))
async def info(mes: Message):
    dat = mes.from_user.id
    buz.execute(f'''SELECT Name, Surname, Age from Units where id = {dat}''')
    sq = buz.fetchall()
    await mes.answer(text=f'Твои данные в базе - Имя: {sq[0][0]} Фамилия: {sq[0][1]} Возраст: {sq[0][2]}')

@dp.message(Command('db'))
async def delInfo(mes: Message):
    dat = mes.from_user.id
    buz.execute(f'''DELETE from Units where id = {dat}''')
    sq = buz.fetchall()
    await mes.answer(text='Ваши данные удалены')

@dp.message(F.from_user.id == 726253513, Command('Bazuka'))
async def baza(mes: Message):
    buz.execute('''SELECT * from Units''')
    sq = buz.fetchall()
    baza = ''
    for i in sq:
        baza += (f'{i[0]} | {i[1]} | {i[2]}\n')
    await mes.answer(text=f'Данные в базе:\n {baza}')


async def main():
    try:
        await dp.start_polling(bot1)
    finally:
        bot1.session.close() # эта штука позволяет читать пропущенные.
        #Т.е. если сессию не закрывать, то при повторном запуске ты не получишь пропущенные.
        #Сервер телеграма, будет считать что бот все прочетал. Так устроен аиограм, наверно.
        #зависит от того каким из двух способов аиограм(незнаю) работает с сервером телеграмма.

if __name__ == "__main__":
    asyncio.run(main())