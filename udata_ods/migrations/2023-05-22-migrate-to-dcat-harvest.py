'''
Migrate ODS harvest sources to a DCAT backend
'''
import logging
from urllib.parse import urlparse

from udata.models import Dataset
from udata.harvest.models import HarvestSource

from udata_ods.harvesters import OdsBackend

log = logging.getLogger(__name__)


ODS_API_PATH = 'api/explore/v2.1'


def dataset_v2_url(source_url, dataset_id):
    return f'{source_url}/{ODS_API_PATH}/catalog/datasets/{dataset_id}'


def dcat_catalog_url(source_url):
    return f'{source_url}/{ODS_API_PATH}/catalog/exports/dcat'


def build_where_clause(filters):
    # TODO: check how to build where clause?
    # TODO: check for inspire
    params = []
    for f in filters:
        ods_key = OdsBackend.FILTERS.get(f['key'], f['key'])
        op = 'NOT ' if f.get('type') == 'exclude' else ''
        params.append(op + ods_key + f'="{f["value"]}"')
    where_clause = 'where=' + ' AND '.join(params)
    return where_clause


def ods_to_dcat_catalog_url(url, config):
    dcat_url = dcat_catalog_url(url)
    if not config['filters']:
        return dcat_url
    where_clause = build_where_clause(config['filters'])
    # TODO: should we urlencode(where_clause)?
    # It would be less readable though
    return f'{dcat_url}/?{where_clause}'


def ods_to_target_url(source_url, dataset_id, resource):
    ods_type = resource.harvest._data.get('ods_type')
    if ods_type == 'api':
        # build new download url
        base_url = dataset_v2_url(source_url, dataset_id)
        return f'{base_url}/exports/{resource.format}'
    if ods_type in ['alternative_export', 'attachment']:
        # replace api path
        # TODO: why is it api/v2 here?
        return resource.url.replace("/api/datasets/1.0/", "/api/v2/catalog/datasets/")
    # Not an ods harvested resource, returning as is
    log.warning(f'Resource {resource} does not have a valid ods_type ({ods_type}). ' +
                'Something may be wrong with this resource.')
    return resource.url


def migrate(db):
    log.info('Processing Harvest Sources.')

    sources = HarvestSource.objects(backend='ods').no_cache().timeout(False)
    sources = sources.filter(id='5b130bb0c751df05bac4e2b0')  # TODO: remove this filter

    dataset_count = 0
    source_count = 0
    for source in sources:
        source_url = source.url.rstrip('/')
        if urlparse(source_url).path != '':
            # TODO: what to do with these?
            log.warning(f'Skipping the source {source.id} (status:{source.validation.state}). ' +
                        f'It has an URL that is not a root ODS URL: {source_url}.')
            continue
        source.backend = 'dcat'
        source.url = ods_to_dcat_catalog_url(source_url, source.config)
        # source.config["filters"] = None  #  TODO: remove now useless config
        source.save()
        source_count += 1

        datasets = Dataset.objects(
            harvest__source_id=str(source.id)
        )
        for dataset in datasets:
            dataset.harvest.backend = 'DCAT'
            # TODO: how to suffix remote_id?
            dataset.harvest.remote_id = f'{dataset.harvest.remote_id}@agenceore'
            dataset.harvest.ods_url = None
            dataset.harvest.ods_references = None
            dataset.harvest.ods_has_records = None
            dataset.harvest.ods_geo = None

            for resource in dataset.resources:
                # Ignore resources that haven't been harvested
                if resource.harvest:
                    remote_id_stripped = dataset.harvest.remote_id.split("@")[0]
                    resource.url = ods_to_target_url(source_url, remote_id_stripped, resource)
                    resource.harvest.ods_type = None

            dataset.save()
            dataset_count += 1

    log.info(f'Modified {source_count} Harvest Sources objects')
    log.info(f'Modified {dataset_count} Dataset objects')
    log.info('Done')
