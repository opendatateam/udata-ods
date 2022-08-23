from udata.api import fields
from udata.core.dataset.api_fields import dataset_harvest_fields, resource_harvest_fields

dataset_harvest_fields['ods_url'] = fields.String(description='The ods url for ods harvested dataset', allow_null=True)
dataset_harvest_fields['ods_references'] = fields.String(description='The ods reference for ods  harvested dataset', allow_null=True)
dataset_harvest_fields['ods_has_records'] = fields.Boolean(description='boolean for ods records', allow_null=True)  # TODO: what description?
dataset_harvest_fields['ods_geo'] = fields.Boolean(description='boolean for ods geo', allow_null=True)  # TODO: what description?

resource_harvest_fields['ods_type'] = fields.String(description='The ods type for ods harvest dataset', allow_null=True)  # TODO: what description?
