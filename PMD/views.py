from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST

from PMD.models import DataSeries
import PMD.forms

import pprint

# We make the dictionary of data series forms
data_series_forms = dict()
for form in PMD.forms.__dict__.values():
	try:
		if form != PMD.forms.DataSeriesForm and issubclass(form, PMD.forms.DataSeriesForm):
			data_series_forms[form.data_series] = form
	except Exception:
		pass

print pprint.pformat(data_series_forms, depth=6)

# Assert we only have get
@require_safe
@login_required
def index(request):
	time_range_form = PMD.forms.TimeRangeForm(label_suffix='')
	return render(request, 'PMD/search_data.html', {'time_range_form': time_range_form, 'data_series_forms': [data_series_forms[name](label_suffix='') for name in sorted(data_series_forms.keys())]})


# Assert we only have get
@require_safe
@login_required
def result_table(request, data_series):
	#print pprint.pformat(request.GET, depth=6)
	#import pdb; pdb.set_trace()
	# We get te result table
	if data_series in data_series_forms:
		if data_series not in request.session:
			request.session[data_series] = dict()
		try:
			result_table = data_series_forms[data_series].get_result_table(request.GET, request.session[data_series], request.GET.get('page', 1))
		except Exception, why:
			return HttpResponseBadRequest(str(why))
	else:
		return HttpResponseBadRequest("Unknown data series %s" % data_series)
	
	return render(request, 'PMD/result_table.html', result_table)

# Assert we only have post
@require_POST
@login_required
def bring_online(request):
	pass


#### OLD stuff ####
@login_required
def old_index(request):
	data_series_list = get_list_or_404(DataSeries)
	if not request.user.is_authenticated():
		print "User is not authenticated:"
	print request.user.username
	return render(request, 'PMD/index.html', {'data_series_list': data_series_list})


# Assert we only have get
@require_safe
@login_required
def old_result_table(request, data_series):
	print pprint.pformat(request.GET, depth=6)
	
	# We get the time range
	try:
		start_date, end_date, cadence = parse_time_range(request)
	except Exception, why:
		return HttpResponseBadRequest(str(why))
	
	# We parse the request
	if data_series in data_series_forms:
		form = data_series_forms[data_series](request.GET)
	else:
		return HttpResponseBadRequest("Unknown Series %s" % data_series)
#	import pdb; pdb.set_trace()
	if form.is_valid():
		# We get the records
		page = request.GET.get('page')
		records = form.records(start_date, end_date, cadence, page)
		return render(request, 'PMD/table_data.html', {'time_range_form': PMD.forms.TimeRangeForm(request.GET), 'data_series_forms': [data_series_forms[name](label_suffix='') for name in sorted(data_series_forms.keys())], 'records' : records})
		#return HttpResponse(str(records), content_type="text/plain")
	else:
		# We need to return some error message
		return HttpResponseBadRequest("Invalid request")
