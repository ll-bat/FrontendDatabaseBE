import random
import string
import psycopg2

from api.middleware import get_user_database
from app.settings import MAIN_DATABASE, MAIN_DATABASE_USER, MAIN_DATABASE_PASSWORD, MAIN_DATABASE_HOST, \
    MAIN_DATABASE_PORT


class UserDatabaseHelper:
    @staticmethod
    def get_table_name(name):
        return '__frontend_database__%s' % name

    @staticmethod
    def prepare_environment():
        user_database = get_user_database()
        conn = psycopg2.connect(
            database=MAIN_DATABASE,
            user=MAIN_DATABASE_USER,
            password=MAIN_DATABASE_PASSWORD,
            host=MAIN_DATABASE_HOST,
            port=MAIN_DATABASE_PORT,
        )
        conn.autocommit = True
        cursor = conn.cursor()
        # noinspection PyBroadException
        try:
            # noinspection SqlDialectInspection
            cursor.execute(f'CREATE DATABASE {user_database}')
        except Exception as e:
            # database already exists
            pass
        conn.close()

    # noinspection PyShadowingNames
    @staticmethod
    def execute(sql, fetchone=False, fetchall=False):
        user_database = get_user_database()
        conn = psycopg2.connect(
            database=user_database,
            user=MAIN_DATABASE_USER,
            password=MAIN_DATABASE_PASSWORD,
            host=MAIN_DATABASE_HOST,
            port=MAIN_DATABASE_PORT,
        )
        conn.autocommit = True
        cursor = conn.cursor()
        # noinspection PyBroadException
        try:
            cursor.execute(sql)
            result = None
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            cursor.close()
            raise e

    @staticmethod
    def fetchone(sql):
        return UserDatabaseHelper.execute(sql, fetchone=True)

    @staticmethod
    def fetchall(sql):
        return UserDatabaseHelper.execute(sql, fetchall=True)

    @staticmethod
    def create_table(name, fields):
        pass


DbHelper = UserDatabaseHelper


def dbname(name):
    return DbHelper.get_table_name(name)


def fetchone(sql):
    return DbHelper.fetchone(sql)


def fetchall(sql):
    return DbHelper.fetchall(sql)


class UtilHelper:
    @staticmethod
    def get_random_string(length):
        result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
        return result_str
