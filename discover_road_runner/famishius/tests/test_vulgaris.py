from django.test import SimpleTestCase


class OtherTest(SimpleTestCase):
    """
    In reality, apps often can have so many tests this is a more practical
    organising pattern.
    """

    def test_success(self):
        self.assertEqual(1 + 1, 2)

