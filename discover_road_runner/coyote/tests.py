import time

from django.contrib.auth.models import User
from django.test import SimpleTestCase

from discover_road_runner.acme.models import Product, Purchase


class FastOutputTest(SimpleTestCase):

    def test_road_runner_is_not_blocked(self):
        self.fail('Road Runner: Debug me now! No waiting, kgo!')

    def test_slow(self):
        time.sleep(3)

    def test_wile_e_is_ord_blocked(self):
        """
        ord('r') < ord('s') < ord('w')
        """
        self.fail('Wile E: I get blocked by teh ASCIIz...')

    def test_coyote_can_purchase(self):
        coyote = User.objects.create_user(username='coyote')
        dynamite = Product.objects.create(name='Dynamite')
        Purchase.objects.create(product=dynamite, quantity=5, user=coyote)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Purchase.objects.count(), 1)
