from django.conf import settings
from django.db import models


class Product(models.Model):
    name = models.TextField()


class Purchase(models.Model):
    product = models.ForeignKey(Product)
    quantity = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
