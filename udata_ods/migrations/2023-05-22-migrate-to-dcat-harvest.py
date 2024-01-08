'''
Migrate ODS harvest sources to a DCAT backend
'''
import logging
import requests
from urllib.parse import urlencode, urlparse

from udata.models import Dataset
from udata.harvest.models import HarvestSource

from udata_ods.harvesters import OdsBackend

log = logging.getLogger(__name__)


ODS_API_PATH = 'api/explore/v2.1'


def dataset_home_url(source_url, dataset_id):
    return f'{source_url}/explore/dataset/{dataset_id}/'


def dataset_v2_url(source_url, dataset_id, format):
    return f'{source_url}/{ODS_API_PATH}/catalog/datasets/{dataset_id}/exports/{format}'


def dcat_catalog_url(source_url):
    return f'{source_url}/{ODS_API_PATH}/catalog/exports/dcat/'


def build_where_clause(filters):
    if not filters:
        return {}
    params = []
    for f in filters:
        ods_key = OdsBackend.FILTERS.get(f['key'], f['key'])
        op = 'NOT ' if f.get('type') == 'exclude' else ''
        params.append(op + ods_key + f'="{f["value"]}"')
    where_clause = {"where": ' AND '.join(params)}
    return where_clause


def ods_to_dcat_catalog_url(url, config):
    dcat_url = dcat_catalog_url(url)
    params = build_where_clause(config.get('filters'))
    params['include_exports'] = 'json,csv,shp,geojson'
    params['lang'] = 'fr'
    return f'{dcat_url}?{urlencode(params)}'


def ods_to_target_url(source_url, dataset_id, resource):
    ods_type = resource.harvest._data.get('ods_type')
    if ods_type == 'api':
        # build new download url
        return dataset_v2_url(source_url, dataset_id, resource.format)
    if ods_type == 'attachment':
        # replace api path: using api/v2 (instead of v2.1) has been confirmed by ODS
        return resource.url.replace("/api/datasets/1.0/", "/api/v2/catalog/datasets/")
    if ods_type == 'alternative_export':
        # Check if final url differs from ODS resource url (ignoring netloc or scheme redirects)
        # Final url will be exposed as downloadURL in DCAT export
        final_url = requests.head(resource.url, allow_redirects=True).url
        if urlparse(final_url).path != urlparse(resource.url).path:
            return final_url
        # replace api path: using api/v2 (instead of v2.1) has been confirmed by ODS
        return resource.url.replace("/api/datasets/1.0/", "/api/v2/catalog/datasets/")
    # Not an ods harvested resource, returning as is
    log.warning(f'Resource {resource.id} does not have a valid ods_type ({ods_type}). ' +
                'Something may be wrong with this resource.')
    return resource.url


def migrate(db):
    log.info('Processing Harvest Sources.')

    sources = HarvestSource.objects(backend='ods').no_cache().timeout(False)

    dataset_count = 0
    source_count = 0
    for source in sources:
        source_url = source.url.rstrip('/')
        if urlparse(source_url).path != '':
            # We are logging a warning on sources that don't have a root ODS url
            log.warning(f'Skipping the source {source.id} (status:{source.validation.state}). ' +
                        f'It has an URL that is not a root ODS URL: {source_url}.')
            continue
        source.backend = 'dcat'
        source.url = ods_to_dcat_catalog_url(source_url, source.config)
        source.config["filters"] = None
        source.save()
        source_count += 1

        datasets = Dataset.objects(
            harvest__source_id=str(source.id)
        ).no_cache().timeout(False)
        for dataset in datasets:
            previous_remote_id = dataset.harvest.remote_id
            dataset.harvest.backend = 'DCAT'
            # remote_id is now the URI of the dataset
            dataset.harvest.remote_id = dataset_home_url(source_url, dataset.harvest.remote_id)
            # removing ODS harvest metadata
            dataset.harvest.ods_url = None
            dataset.harvest.ods_references = None
            dataset.harvest.ods_has_records = None
            dataset.harvest.ods_geo = None

            for resource in dataset.resources:
                # Ignore resources that haven't been harvested
                if resource.harvest:
                    resource.url = ods_to_target_url(source_url, previous_remote_id, resource)
                    resource.harvest.ods_type = None

            dataset.save()
            dataset_count += 1

    log.info(f'Modified {source_count} Harvest Sources objects')
    log.info(f'Modified {dataset_count} Dataset objects')
    log.info('Done')
