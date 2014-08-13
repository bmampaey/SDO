from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from paginator import EstimatedCountPaginator
from DRMS.models import DRMSDataSeries
from DRMS.models import AiaLev1FitsHeader
from DRMS.models import HmiIc45sFitsHeader
from DRMS.models import HmiM45sFitsHeader

class DRMSDataSeriesResource(ModelResource):
	keywords = fields.DictField(readonly=True, attribute='keywords')
	class Meta:
		queryset = DRMSDataSeries.objects.all()
		resource_name = 'data_series'
		fields = ["name", "keywords"]
		filtering = {
			'name': ALL,
		}

class AiaLev1FitsHeaderResource(ModelResource):
	class Meta:
		queryset = AiaLev1FitsHeader.objects.filter(latest__isnull = False)
		resource_name = 'aia.lev1'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}
		paginator_class = EstimatedCountPaginator


class HmiIc45sFitsHeaderResource(ModelResource):
	class Meta:
		queryset = HmiIc45sFitsHeader.objects.filter(latest__isnull = False)
		resource_name = 'hmi.ic_45s'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}
		paginator_class = EstimatedCountPaginator


class HmiM45sFitsHeaderResource(ModelResource):
	class Meta:
		queryset = HmiM45sFitsHeader.objects.filter(latest__isnull = False)
		resource_name = 'hmi.m_45s'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL
		}
		paginator_class = EstimatedCountPaginator
