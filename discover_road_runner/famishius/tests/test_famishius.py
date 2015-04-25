import unittest

from django.contrib.auth.models import User
from django.test import SimpleTestCase

from discover_road_runner.acme.models import Product, Purchase


class CombinedTest(SimpleTestCase):

    def test_success(self):
        self.assertEqual(1 + 1, 2)

    def test_error(self):
        raise ValueError

    def test_fail(self):
        self.fail()

    def test_skip(self):
        self.skipTest('Fix me later?')

    @unittest.expectedFailure
    def test_decorator_expected_fail(self):
        self.fail()

    @unittest.skip
    def test_decorator_skip(self):
        print('Never get here!')

    def test_roadrunner_can_purchase(self):
        roadrunner = User.objects.create_user(username='roadrunner')
        seed = Product.objects.create(name='Bird Seed')
        Purchase.objects.create(product=seed, quantity=9001, user=roadrunner)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Purchase.objects.count(), 1)
