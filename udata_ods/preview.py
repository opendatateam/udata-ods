from flask import url_for

from udata.core.dataset.models import Resource
from udata.core.dataset.preview import PreviewPlugin


class OdsPreview(PreviewPlugin):
    def can_preview(self, resource):
        if not isinstance(resource, Resource):
            return
        dataset = resource.dataset
        if not dataset.harvest or 'ods_url' not in dataset.harvest._data:
            return
        return resource.harvest._data.get('ods_type') == 'api'

    def preview_url(self, resource):
        dataset = resource.dataset
        return url_for('ods.preview', _external=True, _scheme='',
                       domain=dataset.harvest.domain,
                       id=dataset.harvest.remote_id)
