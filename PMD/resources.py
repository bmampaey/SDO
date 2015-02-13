from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
# See http://django-tastypie.readthedocs.org/en/latest/paginator.html why it is important for postgres to have a special paginator
from paginator import EstimatedCountPaginator
from PMD.models import DataSeries
from PMD.models import AiaLev1Record, HmiIc45SRecord, HmiM45SRecord

class DataSeriesResource(ModelResource):
	class Meta:
		queryset = DataSeries.objects.all()
		resource_name = 'data_series'
		filtering = {
			'data_series': ALL,
			'prefered_datasite': ALL
		}
		paginator_class = EstimatedCountPaginator


class AiaLev1Resource(ModelResource):
	class Meta:
		queryset = AiaLev1Record.objects.all()
		resource_name = 'aia_lev1'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'slotnum': ALL,
			'date_obs': ALL,
			'wavelnth': ALL,
			'quality': ALL,
		}
		excludes = ['t_rec_index', 'fsn' ]
		paginator_class = EstimatedCountPaginator


class HmiIc45SResource(ModelResource):
	class Meta:
		queryset = HmiIc45SRecord.objects.all()
		resource_name = 'hmi_ic_45s'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'slotnum': ALL,
			'date_obs': ALL,
			'quality': ALL,
		}
		excludes = ['t_rec_index', 'camera' ]
		paginator_class = EstimatedCountPaginator


class HmiM45SResource(ModelResource):
	class Meta:
		queryset = HmiM45SRecord.objects.all()
		resource_name = 'hmi_m_45s'
		filtering = {
			'recnum': ALL,
			'sunum': ALL,
			'slotnum': ALL,
			'date_obs': ALL,
			'quality': ALL,
		}
		excludes = ['t_rec_index', 'camera' ]
		paginator_class = EstimatedCountPaginator
