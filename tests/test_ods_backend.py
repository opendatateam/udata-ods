# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from os.path import join, dirname
from urlparse import parse_qs, urlparse

import pytest

from udata.models import Dataset, License
from udata.core.organization.factories import OrganizationFactory
from udata.harvest import actions
from udata.harvest.tests.factories import HarvestSourceFactory

from udata_ods.harvesters import OdsBackend

DATA_DIR = join(dirname(__file__), 'data')
DOMAIN = 'etalab-sandbox.opendatasoft.com'
ODS_URL = 'http://{0}'.format(DOMAIN)

pytestmark = pytest.mark.usefixtures('clean_db')


def ods_response(filename):
    filename = join(DATA_DIR, filename)
    with open(filename) as f:
        return f.read()


@pytest.mark.options(PLUGINS=['ods'])
@pytest.mark.frontend()
def test_simple(rmock):
    for license_id in set(OdsBackend.LICENSES.values()):
        License.objects.create(id=license_id, title=license_id)

    org = OrganizationFactory()
    source = HarvestSourceFactory(backend='ods',
                                  url=ODS_URL,
                                  organization=org)

    api_url = ''.join((ODS_URL, '/api/datasets/1.0/search/'))
    rmock.get(api_url, text=ods_response('search.json'),
              headers={'Content-Type': 'application/json'})

    actions.run(source.slug)

    assert parse_qs(urlparse(rmock.last_request.url).query) == {
        'start': ['0'], 'rows': ['50'], 'interopmetas': ['true']
    }

    source.reload()

    job = source.get_last_job()
    assert len(job.items) == 5
    assert job.status == 'done'

    datasets = {d.extras['harvest:remote_id']: d for d in Dataset.objects}
    assert len(datasets) == 3

    assert 'test-a' in datasets
    d = datasets['test-a']
    assert d.title == 'test-a'
    assert d.description == 'test-a-description'
    assert d.tags == ['culture',
                      'environment',
                      'heritage',
                      'keyword1',
                      'keyword2']
    assert d.extras['ods:references'] == 'http://example.com'
    assert d.extras['ods:has_records']
    assert d.extras['harvest:remote_id'] == 'test-a'
    assert d.extras['harvest:domain'] == DOMAIN
    assert d.extras['ods:url'] == 'http://etalab-sandbox.opendatasoft.com/explore/dataset/test-a/'  # noqa
    assert d.license.id == 'fr-lo'

    assert len(d.resources) == 2
    resource = d.resources[0]
    assert resource.title == 'CSV format export'
    assert resource.description is not None
    assert resource.format == 'csv'
    assert resource.mime == 'text/csv'
    assert isinstance(resource.modified, datetime)
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-a/download'
                            '?format=csv&timezone=Europe/Berlin'
                            '&use_labels_for_header=true')
    assert resource.extras['ods:type'] == 'api'

    resource = d.resources[1]
    assert resource.title == 'JSON format export'
    assert resource.description is not None
    assert resource.format == 'json'
    assert resource.mime == 'application/json'
    assert isinstance(resource.modified, datetime)
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-a/download'
                            '?format=json&timezone=Europe/Berlin'
                            '&use_labels_for_header=true')
    assert resource.extras['ods:type'] == 'api'

    # test-b has geo feature
    assert 'test-b' in datasets
    test_b = datasets['test-b']
    assert test_b.tags == ['buildings',
                           'equipment',
                           'housing',
                           'keyword1',
                           'spatial-planning',
                           'town-planning']
    assert len(test_b.resources) == 5
    resource_ids = set([r.id for r in test_b.resources])
    resource = test_b.resources[2]
    assert resource.title == 'GeoJSON format export'
    assert resource.description is not None
    assert resource.format == 'json'
    assert resource.mime == 'application/vnd.geo+json'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-b/download'
                            '?format=geojson&timezone=Europe/Berlin'
                            '&use_labels_for_header=true')
    resource = test_b.resources[3]
    assert resource.title == 'Shapefile format export'
    assert resource.description is not None
    assert resource.format == 'shp'
    assert resource.mime is None
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-b/download'
                            '?format=shp&timezone=Europe/Berlin'
                            '&use_labels_for_header=true')

    resource = test_b.resources[4]
    assert resource.title == 'gtfs.zip'
    assert resource.description == 'GTFS 15/01'
    assert resource.format == 'zip'
    assert resource.mime == 'application/zip'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/test-b/alternative_exports'
                            '/gtfs_zip')
    assert resource.extras['ods:type'] == 'alternative_export'

    # test-c has no data
    assert 'test-c' not in datasets

    # test-d is INSPIRE
    assert 'test-d' not in datasets

    # test-shp-limit has no shp export
    assert 'test-shp-limit' in datasets
    test_shp_limit = datasets['test-shp-limit']
    assert len(test_shp_limit.resources) == 3
    for resource in test_shp_limit.resources:
        assert resource.title != 'Shapefile format export'

    # run one more time (test idempotent and resource update)
    response = ods_response('search.json')
    response = response.replace('gtfs.zip', 'new')
    rmock.get(api_url, text=response,
              headers={'Content-Type': 'application/json'})
    actions.run(source.slug)
    source.reload()
    datasets = {d.extras['harvest:remote_id']: d for d in Dataset.objects}
    assert len(datasets) == 3
    test_b = datasets['test-b']
    assert len(test_b.resources) == 5
    new_resource_ids = set([r.id for r in test_b.resources])
    # resources ids stay the same
    assert new_resource_ids == resource_ids
    resource = test_b.resources[4]
    assert resource.title == 'new'


@pytest.mark.parametrize('url', ['http://domain.com/', 'http://domain.com'])
def test_urls_format(url):
    source = HarvestSourceFactory(url=url)
    backend = OdsBackend(source)

    assert backend.source_url == 'http://domain.com'
    assert backend.api_url == 'http://domain.com/api/datasets/1.0/search/'

    explore_url = backend.explore_url('id')
    download_url = backend.download_url('id', 'format')
    export_url = backend.export_url('id')

    assert explore_url == 'http://domain.com/explore/dataset/id/'
    assert download_url.startswith(explore_url)
    assert export_url.startswith(explore_url)
