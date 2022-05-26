from django.db import models

# Create your models here.
from api.utils import UtilHelper


class UserTokenDatabase(models.Model):
    token = models.CharField(max_length=255)
    database = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_database'

    @staticmethod
    def create_token_and_database():
        token = UtilHelper.get_random_string(255)
        database = 'frontend_database_' + UtilHelper.get_random_string(25)
        UserTokenDatabase(token=token, database=database).save()
        return token, database
