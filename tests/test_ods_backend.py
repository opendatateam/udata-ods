import json

from datetime import datetime, date
from os.path import join, dirname
from urllib.parse import parse_qs, urlparse

import pytest

from udata.models import Dataset, License
from udata.core.organization.factories import OrganizationFactory
from udata.harvest import actions
from udata.harvest.tests.factories import HarvestSourceFactory
from udata.utils import faker

from udata_ods.harvesters import OdsBackend

DATA_DIR = join(dirname(__file__), 'data')
DOMAIN = 'etalab-sandbox.opendatasoft.com'
ODS_URL = 'http://{0}'.format(DOMAIN)
SEARCH_URL = '{0}/api/datasets/1.0/search/'.format(ODS_URL)
DEFAULT_SEARCH = 'test-b', 'test-c', 'test-a', 'test-shp-limit'
HEADERS = {'Content-Type': 'application/json'}


pytestmark = pytest.mark.options(PLUGINS=['ods'])


def dataset_url(id):
    return ''.join((ODS_URL, '/api/datasets/1.0/{0}/'.format(id)))


def ods_dataset(id):
    filename = join(DATA_DIR, '{id}.json'.format(id=id))
    with open(filename) as f:
        return json.load(f)


def ods_search(*datasets):
    datasets = [d if isinstance(d, dict) else ods_dataset(d) for d in datasets]
    return {
        "nhits": len(datasets),
        "parameters": {
            "timezone": "UTC",
            "rows": 10,
            "format": "json",
            "staged": False
        },
        "datasets": datasets
    }


@pytest.fixture(autouse=True)
def _mock_harvest(request, rmock):
    marker = request.node.get_closest_marker('harvest')
    if not marker:
        return
    datasets = []
    for id in marker.args:
        data = ods_dataset(id)
        rmock.get(dataset_url(id), json=data, headers=HEADERS)
        datasets.append(data)
    rmock.get(SEARCH_URL, headers=HEADERS, json=ods_search(*datasets))


def get_qs(request, name):
    return request.qs[name][0]


@pytest.fixture(autouse=True)
def inject_licenses(clean_db):
    for license_id in set(OdsBackend.LICENSES.values()):
        License.objects.create(id=license_id, title=license_id)


@pytest.mark.frontend()
@pytest.mark.harvest(*DEFAULT_SEARCH)
def test_simple(rmock):
    org = OrganizationFactory()
    source = HarvestSourceFactory(backend='ods',
                                  url=ODS_URL,
                                  organization=org)

    actions.run(source.slug)

    search_request = rmock.request_history[0]
    assert parse_qs(urlparse(search_request.url).query) == {
        'start': ['0'], 'rows': ['50'], 'interopmetas': ['true']
    }

    source.reload()

    job = source.get_last_job()
    assert len(job.items) == 4
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
    assert d.last_modified.date() == date(2015, 4, 9)

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
                            '&use_labels_for_header=false')
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
                            '&use_labels_for_header=false')
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
    assert len(test_b.resources) == 7
    resource_ids = set([r.id for r in test_b.resources])
    resource = test_b.resources[2]
    assert resource.title == 'GeoJSON format export'
    assert resource.description is not None
    assert resource.format == 'geojson'
    assert resource.mime == 'application/vnd.geo+json'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-b/download'
                            '?format=geojson&timezone=Europe/Berlin'
                            '&use_labels_for_header=false')
    resource = test_b.resources[3]
    assert resource.title == 'Shapefile format export'
    assert resource.description is not None
    assert resource.format == 'shp'
    assert resource.mime is None
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com/'
                            'explore/dataset/test-b/download'
                            '?format=shp&timezone=Europe/Berlin'
                            '&use_labels_for_header=false')

    resource = test_b.resources[4]
    assert resource.title == 'gtfs.zip'
    assert resource.description == 'GTFS 15/01'
    assert resource.format == 'zip'
    assert resource.mime == 'application/zip'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/test-b/alternative_exports'
                            '/gtfs_zip')
    assert resource.extras['ods:type'] == 'alternative_export'

    resource = test_b.resources[5]
    assert resource.title == 'Documentation'
    assert resource.description is None
    assert resource.format == 'pdf'
    assert resource.mime == 'application/pdf'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/test-b/attachments'
                            '/documentation_pdf')
    assert resource.extras['ods:type'] == 'attachment'

    resource = test_b.resources[6]
    assert resource.title == 'Extra file'
    assert resource.description is None
    assert resource.format == 'xls'
    assert resource.mime == 'application/vnd.ms-excel'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/test-b/attachments'
                            '/extra_xls')
    assert resource.extras['ods:type'] == 'attachment'

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
    data = ods_dataset('test-b')
    data['alternative_exports'][0]['title'] = 'new'
    rmock.get(dataset_url('test-b'), json=data, headers=HEADERS)

    actions.run(source.slug)
    source.reload()

    datasets = {d.extras['harvest:remote_id']: d for d in Dataset.objects}
    assert len(datasets) == 3
    test_b = datasets['test-b']
    assert len(test_b.resources) == 7
    new_resource_ids = set([r.id for r in test_b.resources])
    # resources ids stay the same
    assert new_resource_ids == resource_ids
    resource = test_b.resources[4]
    assert resource.title == 'new'


@pytest.mark.frontend()
@pytest.mark.harvest('with-attachments', 'empty')
def test_no_data():
    org = OrganizationFactory()
    source = HarvestSourceFactory(backend='ods',
                                  url=ODS_URL,
                                  organization=org)

    actions.run(source.slug)

    source.reload()

    job = source.get_last_job()
    assert len(job.items) == 2
    assert job.status == 'done'

    assert Dataset.objects.count() == 1

    d = Dataset.objects.first()

    assert d.title == 'test attachments'
    assert not d.extras['ods:has_records']
    assert d.extras['harvest:remote_id'] == 'with-attachments'

    assert len(d.resources) == 2

    resource = d.resources[0]
    assert resource.title == 'gtfs.zip'
    assert resource.description == 'GTFS 15/01'
    assert resource.format == 'zip'
    assert resource.mime == 'application/zip'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/with-attachments/alternative_exports'
                            '/gtfs_zip')
    assert resource.extras['ods:type'] == 'alternative_export'

    resource = d.resources[1]
    assert resource.title == 'Documentation'
    assert resource.description is None
    assert resource.format == 'pdf'
    assert resource.mime == 'application/pdf'
    assert resource.url == ('http://etalab-sandbox.opendatasoft.com'
                            '/api/datasets/1.0/with-attachments/attachments'
                            '/documentation_pdf')
    assert resource.extras['ods:type'] == 'attachment'


@pytest.mark.frontend()
@pytest.mark.harvest('inspire')
def test_exclude_inspire_default():
    org = OrganizationFactory()
    source = HarvestSourceFactory(backend='ods',
                                  url=ODS_URL,
                                  organization=org)

    actions.run(source.slug)

    source.reload()

    job = source.get_last_job()
    assert len(job.items) == 1
    assert job.status == 'done'

    datasets = {d.extras['harvest:remote_id']: d for d in Dataset.objects}
    assert len(datasets) == 0


@pytest.mark.frontend()
@pytest.mark.harvest('inspire')
def test_with_inspire_enabled():
    org = OrganizationFactory()
    source = HarvestSourceFactory(backend='ods',
                                  url=ODS_URL,
                                  organization=org,
                                  config={'features': {'inspire': True}})

    actions.run(source.slug)

    source.reload()

    job = source.get_last_job()
    assert len(job.items) == 1
    assert job.status == 'done'

    datasets = {d.extras['harvest:remote_id']: d for d in Dataset.objects}
    assert len(datasets) == 1

    assert 'inspire' in datasets


@pytest.mark.frontend()
def test_include_filter(rmock):
    tag = faker.word()

    def is_filtering(request, context):
        assert 'refine.keyword' in request.qs
        assert get_qs(request, 'refine.keyword') == tag
        is_filtering.ok = True
        context.status_code = 200
        return ods_search(*DEFAULT_SEARCH)
    is_filtering.ok = False

    source = HarvestSourceFactory(backend='ods', url=ODS_URL, config={
        'filters': [{'key': 'tags', 'value': tag}]
    })

    rmock.get(SEARCH_URL, text=is_filtering, headers=HEADERS)

    actions.run(source.slug)

    assert is_filtering.ok


@pytest.mark.frontend()
def test_exclude_filter(rmock):
    tag = faker.word()

    def is_filtering(request, context):
        assert 'exclude.keyword' in request.qs
        assert get_qs(request, 'exclude.keyword') == tag
        is_filtering.ok = True
        context.status_code = 200
        return ods_search(*DEFAULT_SEARCH)
    is_filtering.ok = False

    source = HarvestSourceFactory(backend='ods', url=ODS_URL, config={
        'filters': [{'key': 'tags', 'value': tag, 'type': 'exclude'}]
    })

    rmock.get(SEARCH_URL, text=is_filtering, headers=HEADERS)

    actions.run(source.slug)

    assert is_filtering.ok


@pytest.mark.frontend()
def test_multiple_filters(rmock):
    tag1, tag2, tag3, tag4 = [faker.unique_string() for _ in range(4)]

    def is_filtering(request, context):
        assert 'exclude.keyword' in request.qs
        assert 'refine.keyword' in request.qs
        assert tag1 in request.qs['refine.keyword']
        assert tag2 in request.qs['refine.keyword']
        assert tag3 in request.qs['exclude.keyword']
        assert tag4 in request.qs['exclude.keyword']
        is_filtering.ok = True
        context.status_code = 200
        return ods_search(*DEFAULT_SEARCH)
    is_filtering.ok = False

    source = HarvestSourceFactory(backend='ods', url=ODS_URL, config={
        'filters': [
            {'key': 'tags', 'value': tag1},
            {'key': 'tags', 'value': tag2},
            {'key': 'tags', 'value': tag3, 'type': 'exclude'},
            {'key': 'tags', 'value': tag4, 'type': 'exclude'},
        ]
    })

    rmock.get(SEARCH_URL, text=is_filtering, headers=HEADERS)

    actions.run(source.slug)

    assert is_filtering.ok


@pytest.mark.parametrize('url', ['http://domain.com/', 'http://domain.com'])
def test_urls_format(url):
    source = HarvestSourceFactory(url=url)
    backend = OdsBackend(source)

    assert backend.source_url == 'http://domain.com'
    assert backend.api_search_url == 'http://domain.com/api/datasets/1.0/search/'

    explore_url = backend.explore_url('id')
    download_url = backend.download_url('id', 'format')
    export_url = backend.export_url('id')

    assert explore_url == 'http://domain.com/explore/dataset/id/'
    assert download_url.startswith(explore_url)
    assert export_url.startswith(explore_url)
