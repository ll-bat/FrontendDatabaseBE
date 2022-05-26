import threading

THREAD_LOCAL = threading.local()


class APIMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        register_activity_thread(request=request)
        response = self.get_response(request)
        return response


def register_activity_thread(request):
    _klass = get_current_thread_class()
    _klass.request = request


def get_current_thread_class():
    return THREAD_LOCAL
