import unittest
from django.test import SimpleTestCase


class BasicTest(SimpleTestCase):

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
