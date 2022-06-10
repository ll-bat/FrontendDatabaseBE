from django.db import models

# Create your models here.
from api.middleware import get_user_database
from api.utils import UtilHelper


class UserTokenDatabase(models.Model):
    token = models.CharField(max_length=255)
    database = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_database'

    @staticmethod
    def create_token_and_database():
        token = UtilHelper.get_random_string(255)
        database = 'frontend_database_' + UtilHelper.get_random_string(25).lower()
        UserTokenDatabase(token=token, database=database).save()
        return token, database


class DatabaseManager(models.Manager):
    def get_queryset(self):
        database = get_user_database()
        return super(DatabaseManager, self).get_queryset().filter(database=database)


class UserTable(models.Model):
    database = models.CharField(max_length=255)
    name = models.CharField(max_length=120)
    data = models.JSONField()

    objects = DatabaseManager()

    class Meta:
        db_table = 'user_table'

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.database:
            self.database = get_user_database()
        super(UserTable, self).save(force_insert, force_update, using, update_fields)
