import json
import logging
import psycopg2


class Db:
    def __init__(self):
        self.conn = psycopg2.connect(dbname='postgres', user='postgres',
                        password='1111', host='localhost')

        self.cursor = self.conn.cursor()
        logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s %(message)s')

    def create_tabel(self):
        logging.info(f'создание таблицы')
        self.cursor.execute(
            '''CREATE TABLE VACANCYS(
                VACANCY TEXT)''')
        self.conn.commit()

    def update_tabel(self, data):
        insert_query = '''INSERT INTO VACANCYS (VACANCY) 
                VALUES (%s)'''

        self.cursor.execute(insert_query, [data])
        self.conn.commit()

    def clear_tabel(self):
        logging.info(f'удаление таблицы')
        self.cursor.execute('''DELETE FROM VACANCYS''')
        self.conn.commit()

    def get_tabel(self):
        logging.info(f'получение таблицы')
        self.cursor.execute('''SELECT * FROM VACANCYS''')

        vacancys = self.cursor.fetchall()

        vacancyslist = []

        for row in vacancys:
            print(row)
            vacancyslist.append(json.loads(row[0]))

        return vacancyslist