from django.urls import path

from api.views import create_table, table_exists

urlpatterns = [
    path('create-table', create_table),
    path('table-exists', table_exists),
]