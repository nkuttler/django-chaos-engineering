"""
Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_probability(value):
    if not 0 <= value <= 100:
        raise ValidationError(_("Invalid probability of {}".format(value)))
    return value
