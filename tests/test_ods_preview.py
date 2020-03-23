import gc
import pytest

from flask import url_for

from udata.core.dataset.factories import (
    CommunityResourceFactory, DatasetFactory, ResourceFactory
)
from udata.tests.helpers import assert200, assert404
from udata.utils import faker


@pytest.fixture
def no_gc():
    '''Prevent garbage collecting during test with anonymous objects (factories)'''
    gc.disable()
    yield
    gc.collect()
    gc.enable()


pytestmark = [
    pytest.mark.usefixtures('clean_db', 'no_gc'),
    pytest.mark.options(PLUGINS=['ods']),
    pytest.mark.frontend,
]


def test_display_preview_for_api_resources():
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    resource = ResourceFactory(extras={'ods:type': 'api'})
    _ = DatasetFactory(resources=[resource], extras={ # noqa
        'harvest:remote_id': remote_id,
        'harvest:domain': domain,
        'ods:url': faker.uri(),
    })

    assert resource.preview_url == url_for('ods.preview',
                                           domain=domain,
                                           id=remote_id,
                                           _external=True,
                                           _scheme='')


@pytest.mark.parametrize('typ', ['alternative_export', 'attachment'])
def test_no_preview_for(typ):
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    resource = ResourceFactory(extras={'ods:type': typ})
    # affectation prevent garbage collector from removing object before the end of the test
    DatasetFactory(resources=[resource], extras={
        'harvest:remote_id': remote_id,
        'harvest:domain': domain,
        'ods:url': faker.uri(),
    })  

    assert resource.preview_url is None


def test_display_preview_only_for_ods_resources():
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    resource = ResourceFactory(extras={'ods:type': 'api'})
    _ = DatasetFactory(resources=[resource], extras={ # noqa
        'harvest:remote_id': remote_id,
        'harvest:domain': domain,
    })

    assert resource.preview_url is None


def test_no_preview_for_community_resources():
    domain = faker.domain_name()
    remote_id = faker.unique_string()
    dataset = DatasetFactory(extras={
        'harvest:remote_id': remote_id,
        'harvest:domain': domain,
        'ods:url': faker.uri(),
    })
    resource = CommunityResourceFactory(dataset=dataset,
                                        extras={'ods:type': 'api'})

    assert resource.preview_url is None


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
    _ = DatasetFactory(extras={  # noqa
        'harvest:remote_id': remote_id,
        'harvest:domain': domain
    })

    url = url_for('ods.preview', domain=domain, id=remote_id)

    assert404(client.get(url))
