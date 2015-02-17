from django.test import SimpleTestCase


class SkippedOnlyTest(SimpleTestCase):
    def test_skip(self):
        self.skipTest('Test skipped should print app in yellow')
