# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask import url_for

from udata.core.dataset.factories import DatasetFactory
from udata.tests.helpers import assert200, assert404
from udata.utils import faker

pytestmark = [
    pytest.mark.usefixtures('clean_db'),
    pytest.mark.options(PLUGINS=['ods']),
    pytest.mark.frontend()
]


def test_find_and_display_dataset(client, templates):
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    dataset = DatasetFactory(extras={
        'harvest:remote_id': remote_id,
        'harvest:domain': domain
    })

    url = url_for('ods.preview', domain=domain, id=remote_id)

    assert200(client.get(url))
    assert templates.get_context_variable('dataset') == dataset


def test_dataset_not_found(client):
    domain = faker.domain_name()
    remote_id = faker.unique_string()

    url = url_for('ods.preview', domain=domain, id=remote_id)

    assert404(client.get(url))


@pytest.mark.options(PREVIEW_MODE=None)
def test_preview_disabled(client):
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    DatasetFactory(extras={
        'harvest:remote_id': remote_id,
        'harvest:domain': domain
    })

    url = url_for('ods.preview', domain=domain, id=remote_id)

    assert404(client.get(url))
