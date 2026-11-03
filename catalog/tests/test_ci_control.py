from django.test import TestCase


class CIControlTest(TestCase):
    def test_controlled_failure(self):
        self.assertEqual(1, 2, "intentional CI validation failure")
