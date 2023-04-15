import asyncio
import pathlib
import docx
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from bd import Db
from PyPDF2 import PdfReader
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from textanalysis import Analyse
from pars import Hhpars


bot = Bot(token='6179711565:AAEN68i8mQQKe5lZdYyedCkkWixZBelb7sk')#токен для взаимодействия с ботом
dp = Dispatcher(bot, storage=MemoryStorage())#создаём объект класса диспетчера

#класс машины состояний для обработки сообщений


class AcceptNew(StatesGroup):
    mess = State()



#функций для обработки сообщений

@dp.message_handler(Command('start'))#бот получает сообщение /start
async def start(message: types.Message):
    builder = types.ReplyKeyboardMarkup(resize_keyboard=True)#создание клавиатуры
    button = ['Проанализировать резюме']
    builder.add(*button)#создание кнопки и её добавление
    await message.answer('Привет, это бот для анализа резюме!', reply_markup=builder)
    logging.info(f'нажата кнопка start')
    #сообщение пользователю в ответ на команду /start

#функция запускается если была нажата кнопка Проанализировать резюме


@dp.message_handler(Text(equals='Проанализировать резюме'))
async def accept_resume(message: types.Message):

    await AcceptNew.mess.set()#запуск машины сосотояний

    await message.answer('Отправь мне своё резюме текстом, word-файлом или pdf')
    logging.info(f'ожидание отправки резюме')


#после завршения предыдущей функции, в ответ на любое пользовательское соглашение будет запущена эта функция
@dp.message_handler(state=AcceptNew.mess, content_types=types.ContentTypes.ANY)
async def accept_any(message: types.Message, state: FSMContext):
    logging.info(f'обработка файла резюме')
    #в if условии определяется текстоовое ли сообщение или это файл

    if message.text != None:

        #если текстовое то резюме заносится в строку

        resumestr = message.text

        #в дальнейшем тут будут вызываться функции класса анализатора текста

    else:
        name = message.document.file_name
        await bot.download_file_by_id(message.document.file_id, name)
        extension = pathlib.Path(name).suffix

        #обработка pdf
        if extension == '.pdf':
            reader = PdfReader(name)
            num_of_pages = len(reader.pages)
            resumestr = ''
            for page in range(num_of_pages):

                resumestr += reader.pages[page].extract_text()

        #обработка doc
        else:
            doc = docx.Document(name)
            resumestr = []

            for el in doc.paragraphs:
                resumestr.append(el.text)

            resumestr = ''.join(resumestr)

    await message.answer('Начинаю анализ')



    print(processing_resume(resumestr))

    await state.finish()  # отключение машины состояний

def processing_resume(resumestr):
    logging.info(f'анализ резюме')
    db = Db()
    analyse = Analyse()

    logging.info(f'обработка резюме и вакансий')
    vacancyslist = db.get_tabel()  # получаем список вакансий с помощью hh - pars.py

    prepearedresume = list(
        analyse.prepare(resumestr))  # обрабатываем резюме с помощьб класса analyse - textanalysis

    reslist = []

    for i in range(len(vacancyslist)):
        vacancyslist[i]['requirements'] = analyse.prepare(
            vacancyslist[i]['requirements'])  # обрабаытваем каждую вакансию с помощью analyse

    logging.info(f'поиск количества совпадений')
    # проходим по требованиям каждой вакансии и считаем кол-во совпадений с нашим резюме
    for i in range(len(vacancyslist)):
        requirement = vacancyslist[i]['requirements']
        count = 0
        if len(requirement) == 0: continue
        for j in requirement:
            for word in prepearedresume:
                if j == word:
                    count += 1

        procent = (count / (len(requirement) + len(prepearedresume)))
        if procent * 100 >= 3:
            reslist.append((vacancyslist[i]['vacancy_name'], vacancyslist[i]['requirements'], count))
    logging.info(f'вывод вакансий')
    return reslist

def update_vacancys():
    vacancys = Hhpars()
    vacancys.GetVacancy()
    logging.info(f'обновление списка вакансий')

async def main():
    await dp.start_polling(bot)#функция для запуска бота
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_vacancys, 'interval', hours=24)
    scheduler.start()
    logging.info(f'запуск бота')


if __name__ == "__main__":
    logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(message)s')
    asyncio.run(main())#функция для запуска кода
