import itertools
import json
import os
from abc import abstractmethod

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
    def get_user_models_file(app_path=None):
        if not app_path:
            app_path = UserDatabaseHelper.get_user_app_path()
        models_path = os.path.join(app_path, 'models.py')
        return models_path

    @staticmethod
    def get_user_app_path(app=None):
        if not app:
            app = get_user_database()
        app_path = f'__apps__/{app}'
        return app_path

    @staticmethod
    def add_app_if_not_exists(app):
        app_path = UserDatabaseHelper.get_user_app_path(app)
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
            try:
                with transaction.atomic():
                    table_model = UserTable(name=name, data=received_table_data.to_json())
                    table_model.save()
                    UserDatabaseHelper.build_user_models_file()
            except Exception as e:
                raise e
        else:
            saved_table_data = TableData.from_json(existing_table_model.data)
            if received_table_data != saved_table_data:
                try:
                    with transaction.atomic():
                        existing_table_model.data = received_table_data.to_json()
                        existing_table_model.save()
                        UserDatabaseHelper.build_user_models_file()
                except Exception as e:
                    raise e

    @staticmethod
    def write_to_user_models_file(content, models_file=None):
        if not models_file:
            models_file = UserDatabaseHelper.get_user_models_file()
        with open(models_file, 'w') as file:
            file.write(content)

    @staticmethod
    def build_user_models_file():
        user_table_models = UserTable.objects.all()
        table_models = [TableData.from_json(model.data) for model in user_table_models]
        content_list = [
            'from django.db import models\n\n\n',
            *[model.build_to_write() + '\n\n' for model in table_models]
        ]
        content = ''.join(content_list)
        UserDatabaseHelper.write_to_user_models_file(content)


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

    def get_name(self) -> str:
        return self.name

    def get_fields(self):
        self._sort_fields()
        return self._fields

    def _sort_fields(self):
        if self._fields_sorted is False:
            self._fields.sort(key=lambda f: f.name)
            self._fields_sorted = True

    def build_fields(self, fields):
        for name in fields:
            config = fields[name]
            type = config['type']
            params = config['params']
            field_class = TableFieldFactory.create(name, type, params)
            self._fields.append(field_class)
        self._sort_fields()

    def to_json(self):
        fields_dict = {}
        for field in self.get_fields():
            fields_dict[field.name] = field.to_dict()
        return json.dumps({'name': self.name, 'fields': fields_dict})

    @staticmethod
    def from_json(json_data):
        """
        json_data: {
            'name': 'table-name',
            'fields': {
                'id': {
                    'type' : '',
                    'params': {
                        ...
                    }
                }
            }
        }
        """
        data = json.loads(json_data)
        return TableData(data)

    def build_to_write(self):
        content_list = [
            f"class {self.get_name().capitalize()}(models.Model):",
            *['    ' + field.build_to_write() for field in self.get_fields()],
            '',
            f'    class Meta:',
            f'        db_table = "{self.get_name()}"'
        ]
        return '\n'.join(content_list)

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


class AbstractTableField:
    def __init__(self, name, params):
        self.name = name
        self._params = params
        self._default_length = 255
        self._default_nullable = True
        self._default_value = ''
        self.length = self._get_length(params)
        self.nullable = self._get_nullable(params)
        self.default_value = self._get_default_value(params)

    def _get_length(self, params):
        length = params.get('length', None)
        if isinstance(length, int):
            return length
        return self._default_length

    def _get_nullable(self, params):
        nullable = params.get('nullable', None)
        if nullable is None:
            return self._default_nullable
        return True if nullable else False

    def _get_default_value(self, params):
        default_value = params.get('default_value', None)
        if isinstance(default_value, str):
            return default_value
        return self._default_value

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.get_type(),
            'params': self.get_params()
        }

    @staticmethod
    def from_dict(config):
        name = config['name']
        type = config['type']
        params = config['params']
        return TableFieldFactory.create(name, type, params)

    @abstractmethod
    def get_type(self) -> str:
        raise Exception('implement in child class')

    @abstractmethod
    def get_params(self) -> dict:
        raise Exception('implement in child class')

    @abstractmethod
    def build_to_write(self) -> str:
        raise Exception('implement in child class')

    def __eq__(self, other):
        if not isinstance(other, AbstractTableField):
            return False

        self_dict = self.to_dict()
        other_dict = other.to_dict()

        return json.dumps(self_dict, sort_keys=True) == json.dumps(other_dict, sort_keys=True)

    def __repr__(self):
        return f'{self.get_type()}({self.name}, ' \
               f'({self.length}, {self.nullable}, {self._default_value}))'


class PrimaryKeyField(AbstractTableField):
    def __init__(self, name, params):
        super(PrimaryKeyField, self).__init__(name, params)

    def get_type(self):
        return TABLE_FIELD_PRIMARY_KEY_FIELD

    def get_params(self) -> dict:
        return {}

    def build_to_write(self) -> str:
        return f'{self.name} = models.IntegerField(primary_key=True)'


class CharField(AbstractTableField):
    def __init__(self, name, params):
        super(CharField, self).__init__(name, params)

    def get_type(self):
        return TABLE_FIELD_CHAR_FIELD

    def get_params(self) -> dict:
        return {
            'length': self.length,
            'nullable': self.nullable,
            'default_value': self.default_value,
        }

    def build_to_write(self) -> str:

        return f'{self.name} = models.CharField(max_length={self.length}, null={self.nullable}, ' \
               f'blank={self.nullable}, default="{self.default_value}")'


class BooleanField(AbstractTableField):
    def __init__(self, name, params):
        super(BooleanField, self).__init__(name, params)

    def get_type(self):
        return TABLE_FIELD_CHAR_FIELD

    def get_params(self) -> dict:
        return {
            'length': self.length,
            'nullable': self.nullable,
            'default_value': self.nullable,
        }

    def build_to_write(self) -> str:
        return f'{self.name} = models.BooleanField(null={self.nullable}, blank={self.nullable}, ' \
               f'default="{self.default_value}")'


TABLE_FIELD_PRIMARY_KEY_FIELD = 'PrimaryKeyField'
TABLE_FIELD_CHAR_FIELD = 'CharField'
TABLE_FIELD_BOOLEAN_FIELD = 'BooleanField'


class TableFieldFactory:
    @staticmethod
    def create(name, type, params):
        if type == TABLE_FIELD_PRIMARY_KEY_FIELD:
            return PrimaryKeyField(name, params)
        elif type == TABLE_FIELD_CHAR_FIELD:
            return CharField(name, params)
        elif type == TABLE_FIELD_BOOLEAN_FIELD:
            return BooleanField(name, params)
        else:
            raise Exception('not such field ' + type)


DbHelper = UserDatabaseHelper


def dbname(name):
    return DbHelper.get_table_name(name)


def fetchone(sql):
    return DbHelper.fetchone(sql)


def fetchall(sql):
    return DbHelper.fetchall(sql)
