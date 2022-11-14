from flask import abort, current_app, render_template, Blueprint

from udata.core.dataset.models import Dataset

blueprint = Blueprint('ods', __name__, url_prefix='/ods',
                      template_folder='templates')


@blueprint.route('/preview/<domain>/<id>')
def preview(domain, id):
    if current_app.config.get('PREVIEW_MODE') is None:
        abort(404)
    dataset = Dataset.objects(harvest__remote_id=id, harvest__domain=domain).first()
    if not dataset:
        abort(404)
    return render_template('preview.html', dataset=dataset)
