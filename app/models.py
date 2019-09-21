from django.db import models


# Create your models here.
class Goods(models.Model):
    goods_name = models.CharField(max_length=32)
    goods_price = models.FloatField()


class Order(models.Model):
    order_number = models.CharField(max_length=64)
    status_choices = ((0, '未支付'), (1, '已支付'))
    order_status = models.IntegerField(choices=status_choices, default=0)
    goods = models.ForeignKey(to='Goods', on_delete=models.CASCADE)
