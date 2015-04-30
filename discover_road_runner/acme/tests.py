import unittest

from django.test import SimpleTestCase


class SkippedOnlyTest(SimpleTestCase):
    def test_skip(self):
        self.skipTest('Test skipped should print app in yellow')

    @unittest.expectedFailure
    def test_expected_fail(self):
        self.fail('Expect to fail')

    @unittest.expectedFailure
    def test_unexpected_success(self):
        pass
