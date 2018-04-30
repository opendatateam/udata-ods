# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for

from udata.core.dataset.models import Resource
from udata.core.dataset.preview import PreviewPlugin


class OdsPreview(PreviewPlugin):
    def can_preview(self, resource):
        if not isinstance(resource, Resource):
            return
        dataset = resource.dataset
        if not dataset.extras.get('ods:url'):
            return
        return resource.extras.get('ods:type') == 'api'

    def preview_url(self, resource):
        dataset = resource.dataset
        return url_for('ods.preview', _external=True, _scheme='',
                       domain=dataset.extras['harvest:domain'],
                       id=dataset.extras['harvest:remote_id'])
