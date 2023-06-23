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
from pars import Pars
from ner_alg import Ner_skills
n = Ner_skills()

bot = Bot(token='6179711565:AAEN68i8mQQKe5lZdYyedCkkWixZBelb7sk')  # токен для взаимодействия с ботом
dp = Dispatcher(bot, storage=MemoryStorage())  # создаём объект класса диспетчера


# класс машины состояний для обработки сообщений

class AcceptNew(StatesGroup):
    mess = State()


# функций для обработки сообщений

@dp.message_handler(Command('start'))  # бот получает сообщение /start
async def start(message: types.Message):
    builder = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание клавиатуры
    button = ['Проанализировать резюме']
    builder.add(*button)  # создание кнопки и её добавление
    await message.answer('Привет, это бот для анализа резюме!', reply_markup=builder)
    logging.info(f'нажата кнопка start')
    # сообщение пользователю в ответ на команду /start


# функция запускается если была нажата кнопка Проанализировать резюме


@dp.message_handler(Text(equals='Проанализировать резюме'))
async def accept_resume(message: types.Message):
    await AcceptNew.mess.set()  # запуск машины сосотояний

    await message.answer('Отправь мне своё резюме текстом, word-файлом или pdf')
    logging.info(f'ожидание отправки резюме')


# после завршения предыдущей функции, в ответ на любое пользовательское соглашение будет запущена эта функция
@dp.message_handler(state=AcceptNew.mess, content_types=types.ContentTypes.ANY)
async def accept_any(message: types.Message, state: FSMContext):
    from salary_counting import Count
    logging.info(f'обработка файла резюме')
    # в if условии определяется текстоовое ли сообщение или это файл

    if message.text != None:

        # если текстовое то резюме заносится в строку

        resumestr = message.text

        # в дальнейшем тут будут вызываться функции класса анализатора текста

    else:
        name = message.document.file_name
        await bot.download_file_by_id(message.document.file_id, name)
        extension = pathlib.Path(name).suffix

        # обработка pdf
        if extension == '.pdf':
            reader = PdfReader(name)
            num_of_pages = len(reader.pages)
            resumestr = ''
            for page in range(num_of_pages):
                resumestr += reader.pages[page].extract_text()

        # обработка doc
        else:
            doc = docx.Document(name)
            resumestr = []

            for el in doc.paragraphs:
                resumestr.append(el.text)

            resumestr = ''.join(resumestr)

    await message.answer('Начинаю анализ')

    #1-ый метод

    res = processing_resume(resumestr)

    resume_skill_vector = n.find_words(resumestr)

    if not len(res):
        await message.answer(f'Подходящих вакансий не найдено :(')
        await state.finish()

    await message.answer('Вакансии полученные 1-ым методом:')

    print(res)

    for i in range(len(res)):
        add_res = {'Название вакансии:': res[i][0], 'Зарплата:': 0, 'Ссылка:': res[i][3]}

        if type(res[i][2]) == dict:
            max_salary = res[i][2]['to']
            min_salary = res[i][2]['from']

            if max_salary and min_salary is None:
                add_res['Зарплата:'] = 'Не указана'

            elif max_salary is None:
                add_res['Зарплата:'] = min_salary

            elif min_salary is None:
                add_res['Зарплата:'] = max_salary

            else:
                add_res['Зарплата:'] = (max_salary + min_salary) // 2

        else:
            add_res['Зарплата:'] = 'Не указана'

        res_str = ''
        for k, v in add_res.items():
            res_str += f'{k} {v}\n'

        skill_vector = ner_process(resume_skill_vector, res[i][1])

        if skill_vector:
            res_str += 'Рекомендации по скиллам(ключевые слова): \n'
            for el in skill_vector[:5]:
                res_str += f'{el}, '


        await message.answer(res_str)

    await message.answer('Ожидание 2-ого метода...(может занять несколько минут)')

    c = Count(resumestr)
    c.fill_req()
    final_vacancys, salary = c.get_rec_v_and_salary()

    await message.answer('Вакансии полученные 2-ым методом:')

    await message.answer(f'Ваша предполагаемая зарплата: {salary}')

    for vacancy in final_vacancys:
        skill_vector = ner_process(resume_skill_vector, vacancy['требования'])
        vacancy_res = ''
        for k, v in vacancy.items():
            if k != 'требования':
                vacancy_res += f'{k} {v}\n'

        if skill_vector:
            vacancy_res += 'Рекомендации по скиллам(ключевые слова): \n'
            for el in skill_vector[:5]:
                vacancy_res += f'{el}, '

        await message.answer(vacancy_res)

    await state.finish()  # отключение машины состояний

def ner_process(resume, vacancy):
    from ner_alg import Ner_skills
    n = Ner_skills()

    if vacancy:
        skill_vector = list(n.find_words(vacancy) - resume)

        if skill_vector:
            return skill_vector

        return []

    else:
        return []

def processing_resume(resumestr):
    logging.info(f'анализ резюме')
    db = Db()
    analyse = Analyse()
    from math_method import Math_method
    mm = Math_method(resumestr)

    if not db.check_tabel_exist():
        db.create_tabel()

    if db.check_tabel_void() == 0:
        vacancys = Pars()
        vacancys.get_vacancy()

    reslist = mm.procent_count()

    return reslist


def update_vacancys():
    vacancys = Pars()
    vacancys.get_vacancy()
    logging.info(f'обновление списка вакансий')


async def main():
    await dp.start_polling(bot)  # функция для запуска бота
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_vacancys, 'interval', hours=24)
    scheduler.start()
    logging.info(f'запуск бота')


if __name__ == "__main__":
    logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(message)s')
    asyncio.run(main())  # функция для запуска кода
