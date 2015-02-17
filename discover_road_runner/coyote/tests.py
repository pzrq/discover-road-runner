import time
from django.test import SimpleTestCase


class FastOutputTest(SimpleTestCase):

    def test_road_runner_is_not_blocked(self):
        self.fail('Road Runner: Debug me now! No waiting, kgo!')

    def test_slow(self):
        time.sleep(3)

    def test_wiley_is_not_blocked(self):
        self.fail('Wiley: I get blocked by the ASCII...')
