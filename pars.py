import requests  # для запроса к hh api
import json  # для обработки
import logging
from bd import Db


class Hhpars():
    def __init__(self):
        self.baseurl = 'https://api.hh.ru/'  # url hh для получения вакансий
        logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(message)s')

    def GetPage(self, page):
        # формирование и отправка запроса
        params = {
            'area': 1,
            'page': page,
            'per_page': 100
        }
        req = requests.get(self.baseurl + 'vacancies', params)
        data = req.content.decode()
        req.close()

        logging.info(f'получение вакансий с {page} страницы')

        return(data)

    def GetVacancy(self):
        # обработка запроса добавляем информацию о вакансии в список каждый элемент которого является вакансией

        logging.info(f'получение вакансий')

        db = Db()

        db.clear_tabel()

        for page in range(0, 20):
            js = json.loads(self.GetPage(page))
            for i in range(len(js['items'])):
                logging.info(f'запись в бд')

                db.update_tabel(json.dumps({'vacancy_name': str(js['items'][i]['name']),
                                     'requirements': str(js['items'][i]['snippet']['requirement']),
                                     'salary': str(js['items'][i]['salary']),
                                     'url': str(js['items'][i]['url']),
                                     'employer': str(js['items'][i]['employer'])
                                     }))

t1 = Hhpars()
t1.GetVacancy()