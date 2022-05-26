from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError


def create_table(request):
    return HttpResponse(content="implement this method")


@api_view(['get'])
def table_exists(request):
    name = request.GET.get('name', False)
    if not name:
        raise ValidationError({'non_field_errors': {'name': 'please provide table name'}})
    return HttpResponse(content=" this method")
