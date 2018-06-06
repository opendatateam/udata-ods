# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.models import db, Dataset, Resource

Dataset.extras.register('ods:url', db.URLField)
Dataset.extras.register('ods:references', db.StringField)
Dataset.extras.register('ods:has_records', db.BooleanField)
Dataset.extras.register('ods:geo', db.BooleanField)

# TODO: handle choices
Resource.extras.register('ods:type', db.StringField)
