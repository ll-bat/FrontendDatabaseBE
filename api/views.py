import traceback

from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.helpers import dbname, fetchone, DbHelper


@api_view(['post'])
def create_table(request):
    name = request.data.get("name", None)
    fields = request.data.get("fields", None)
    if not name or not fields:
        raise ValidationError({'non_fields_errors': {'name': 'please provide name and fields'}})
    try:
        DbHelper.create_table(name, fields)
    except Exception as e:
        from pprint import pprint
        print('')
        print('PPRINT')
        print('')
        print('')
        print('')
        pprint(str(e))
        pprint(traceback.format_exc())
        print('')
        print('')
        print('')
        raise ValidationError({'non_field_errors': {'name': "Can't create table"}})
    return Response("implement this method")


@api_view(['get'])
def table_exists(request):
    name = request.query_params.get('name', None)
    if not name:
        raise ValidationError({'non_field_errors': {'name': 'please provide table name'}})
    # noinspection PyBroadException
    try:
        # noinspection SqlDialectInspection
        data = fetchone('select * from %s' % name)
        return Response(True)
    except Exception as e:
        return Response(False)
