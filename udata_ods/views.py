# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, current_app, render_template, Blueprint

from udata.core.dataset.models import Dataset

blueprint = Blueprint('ods', __name__, url_prefix='/ods',
                      template_folder='templates')


@blueprint.route('/preview/<domain>/<id>')
def preview(domain, id):
    if current_app.config.get('PREVIEW_MODE') is None:
        abort(404)
    dataset = Dataset.objects(__raw__={
        'extras.harvest:remote_id': id,
        'extras.harvest:domain': domain
    }).first()
    if not dataset:
        abort(404)
    return render_template('preview.html', dataset=dataset)
