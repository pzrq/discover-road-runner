import time
from django.test import SimpleTestCase


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
