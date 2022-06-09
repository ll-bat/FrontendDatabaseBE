import threading
from django.http import HttpResponseForbidden

THREAD_LOCAL = threading.local()


class APIMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    # noinspection PyMethodMayBeStatic
    def validate_request(self, request):
        user_token = request.headers.get('Authorization', None)
        if user_token is None:
            return False
        from api.models import UserTokenDatabase
        if UserTokenDatabase.objects.filter(token=user_token).count() < 1:
            return False
        return True

    def __call__(self, request):
        if not self.validate_request(request):
            return HttpResponseForbidden(content='Please, provide user_token')
        init_thread(request)
        from api.helpers import UserDatabaseHelper
        UserDatabaseHelper.prepare_environment()
        response = self.get_response(request)
        return response


def init_thread(request):
    token = request.headers['Authorization']
    from api.models import UserTokenDatabase
    model = UserTokenDatabase.objects.filter(token=token).get()
    _klass = get_current_thread_class()
    _klass.request = request
    _klass.user_token = token
    _klass.database = model.database


def get_user_token():
    _klass = get_current_thread_class()
    return _klass.user_token


def get_user_database():
    _klass = get_current_thread_class()
    return _klass.database


def get_current_thread_class():
    return THREAD_LOCAL

