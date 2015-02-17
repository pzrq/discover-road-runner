from django.test import SimpleTestCase


class SuccessfulAppTest(SimpleTestCase):
    def test_exclusively_success(self):
        self.assertEqual(1 + 1, 2)
