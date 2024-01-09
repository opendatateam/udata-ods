
'''
Remove ODS resources that are duplicate of resource with one slash only
'''
import logging

from udata.models import Dataset
from udata.harvest.models import HarvestSource

log = logging.getLogger(__name__)


def migrate(db):
    log.info('Processing Harvest Sources.')

    # sources with trailing slash
    sources = HarvestSource.objects(
        url__regex="/$",
        backend="ods",
        created_at__lte="2018-05-01").no_cache().timeout(False)
    for source in sources:
        log.info(f'Processing source {source} ({source.id})')
        for dat in Dataset.objects(harvest__source_id=str(source.id),
                                   resources__url__contains=source.url + '/'):
            to_delete = []
            for res in dat.resources:
                log.info(res.url)
                # Check if this resource has the double slash due to the source url
                if not source.url + '/' in res.url:
                    continue
                # Check if the same resource exists with a single slash
                one_slash_url = res.url.replace(source.url, source.url.rstrip('/'))
                if any(r.url == one_slash_url for r in dat.resources):
                    to_delete.append(res)
                    log.info('->: DELETE')
            for res in to_delete:
                dat.remove_resource(res)
            dat.save()
