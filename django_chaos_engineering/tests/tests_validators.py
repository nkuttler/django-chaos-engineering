from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from django_chaos_engineering import validators


class ValidatorTest(TestCase):
    def test_valid_100(self):
        self.assertEqual(100, validators.validate_probability(100))

    def test_valid_0(self):
        self.assertEqual(0, validators.validate_probability(0))

    def test_valid_decimal(self):
        value = Decimal("99.999999")
        self.assertEqual(value, validators.validate_probability(value))

    def test_invalid_101(self):
        with self.assertRaises(ValidationError):
            self.assertFalse(validators.validate_probability(101))
