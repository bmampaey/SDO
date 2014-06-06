from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST


from PMD.models import DataSeries
import PMD.forms

# We make the dictionary of data series forms
data_series_forms = dict()
for form in PMD.forms.__dict__.values():
	try:
		if form != PMD.forms.DataSeriesForm and issubclass(form, PMD.forms.DataSeriesForm):
			data_series_forms[form.name] = form
	except Exception:
		pass

import pprint
print pprint.pformat(data_series_forms, depth=6)

@login_required
def old_index(request):
	data_series_list = get_list_or_404(DataSeries)
	if not request.user.is_authenticated():
		print "User is not authenticated:"
	print request.user.username
	return render(request, 'PMD/index.html', {'data_series_list': data_series_list})

# Assert we only have post
@require_POST
@login_required
def bring_online(request):
	pass

# Assert we only have get
@require_safe
@login_required
def index(request):
	
	time_range_form = PMD.forms.TimeRangeForm()
	return render(request, 'PMD/search_data.html', {'time_range_form': time_range_form, 'data_series_forms': [data_series_forms[name](name) for name in sorted(data_series_forms.keys())]})

def parse_time_range(request):
	"""Parse the time range form fields from a reuqest"""
	form = PMD.forms.TimeRangeForm(request.GET)
	form_is_valid = form.is_valid()
	
	if 'start_date' in request.session:
		start_date = request.session['start_date']
	elif form_is_valid:
		start_date = form.cleaned_data['start_date']
		request.session['start_date'] = start_date
	else:
		raise Exception("Missing start_date")
	
	if 'end_date' in request.session:
		end_date = request.session['end_date']
	elif form_is_valid:
		end_date = form.cleaned_data['end_date']
		request.session['end_date'] = end_date
	else:
		raise Exception("Missing end_date")
	
	if 'cadence' in request.session:
		cadence = request.session['cadence']
	elif form_is_valid and 'cadence' in form.cleaned_data:
		cadence = form.cleaned_data['cadence']
		request.session['cadence'] = cadence
	else:
		cadence = None
	
	if cadence is not None and form_is_valid and 'cadence_multiplier' in form.cleaned_data:
		cadence *= form.cleaned_data['cadence_multiplier']
		request.session['cadence'] = cadence
	
	return start_date, end_date, cadence



# Assert we only have get
@require_safe
@login_required
def search_aia_lev1(request):
	
	# We get the time range
	try:
		start_date, end_date, cadence = parse_time_range(request)
	except Exception, why:
		return HttpResponseBadRequest(str(why))
	
	# We parse the request
	form = PMD.forms.AiaLev1SearchForm(request.GET)
	
	if form.is_valid():
		
		best_quality = data_series_form.cleaned_data['best_quality']
		wavelengths = data_series_form.cleaned_data['wavelengths']
		# We return the requested data 
		#return HttpResponseRedirect('PMD/')
		return HttpResponse(str(data_series_form.cleaned_data), content_type="text/plain")
	else:
		# We need to return some error message
		return HttpResponseBadRequest("Invalid request")
