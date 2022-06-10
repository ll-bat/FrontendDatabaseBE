import itertools
import json
import os
import random
import string
import psycopg2
from django.db import transaction

from api.middleware import get_user_database
from api.models import UserTable
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
    def add_app_if_not_exists(app):
        app_path = f'__apps__/{app}'
        if not os.path.isdir(app_path):
            try:
                """
                    app: 
                        migrations
                        __init__.py
                        models.py
                """
                os.makedirs(app_path)
                # create migrations file
                files_to_create = [
                    'migrations',
                    '__init__.py',
                    'models.py',
                ]
                for file_or_dir in files_to_create:
                    if file_or_dir.endswith('.py'):
                        f = open(f'{app_path}/{file_or_dir}', 'a')
                        f.close()
                    else:
                        os.makedirs(f'{app_path}/{file_or_dir}')
            except Exception as e:
                # handle error
                pass

    @staticmethod
    def build_table_from_data(data):
        return TableData(data)

    @staticmethod
    def create_table(name, fields):
        db = get_user_database()
        UserDatabaseHelper.add_app_if_not_exists(db)
        received_table_data = UserDatabaseHelper.build_table_from_data({'name': name, 'fields': fields})
        existing_table_model = UserTable.objects.filter(name=name).first()
        if not existing_table_model:
            with transaction.atomic():
                UserTable(name=name, data=received_table_data.to_json()).save()
        else:
            saved_table_data = TableData.from_json(existing_table_model.data)
            if received_table_data == saved_table_data:
                # ok
                return

            raise Exception('Implement logic for table/model creation')

class TableData:
    """
    data: {
        'name': 'users',
        'fields': {
            'id': {
                'name': 'PrimaryKeyFields',
                'params': {}
            },
            'username': {
                'name': 'CharField',
                'params': {
                    'length': 255,
                    'nullable': True,
                    'default_value': '',
                }
            }
        }
    }
    """

    def __init__(self, data):
        self.name = data['name']
        self._fields = []
        self._fields_sorted = False
        self._orig_fields = data['fields']
        self.build_fields(data['fields'])

    def get_name(self):
        return self.name

    def get_fields(self):
        self._sort_fields()
        return self._fields

    def _sort_fields(self):
        if self._fields_sorted is False:
            self._fields.sort(key=lambda f: f.name)
            self._fields_sorted = True

    def build_fields(self, fields):
        for field in fields:
            config = fields[field]
            name = field
            type = config['type']
            params = config['params']
            field_class = TableField(name, type, params)
            self._fields.append(field_class)
        self._sort_fields()

    def to_json(self):
        fields_dict = {}
        for field in self.get_fields():
            fields_dict[field.name] = field.to_dict()
        return json.dumps({'name': self.name, 'fields': fields_dict})

    @staticmethod
    def from_json(json_data):
        data = json.loads(json_data)
        return TableData(data)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.get_name() != other.get_name():
            return False

        self_fields = self.get_fields()
        other_fields = other.get_fields()
        for self_field, other_field in itertools.zip_longest(self_fields, other_fields, fillvalue=None):
            if self_field != other_field:
                return False

        return True

    def __repr__(self):
        return f"TableData<{self.get_name()}, " \
               f"fields: {', '.join(str(field) for field in self.get_fields())}>"


class TableField:
    # noinspection PyShadowingBuiltins
    def __init__(self, name, type, params):
        self.name = name
        self.type = type
        self.length = None
        self.nullable = None
        self.default_value = None
        self.set_config(params)
        self.validate()

    def set_config(self, config):
        self.length = config.get('length')
        self.nullable = config.get('nullable')
        self.default_value = config.get('default_value')

    def validate(self):
        pass

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'params': {
                'length': self.length,
                'nullable': self.nullable,
                'default_value': self.default_value,
            }
        }

    @staticmethod
    def from_dict(dict):
        name = dict['name']
        type = dict['type']
        params = dict['params']
        return TableField(name, type, params)

    def __eq__(self, other):
        if not isinstance(other, TableField):
            return False

        self_dict = self.to_dict()
        other_dict = other.to_dict()

        return json.dumps(self_dict, sort_keys=True) == json.dumps(other_dict, sort_keys=True)

    def __repr__(self):
        return f'{self.type}({self.name})'


DbHelper = UserDatabaseHelper


def dbname(name):
    return DbHelper.get_table_name(name)


def fetchone(sql):
    return DbHelper.fetchone(sql)


def fetchall(sql):
    return DbHelper.fetchall(sql)
