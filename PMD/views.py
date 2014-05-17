from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from PMD.models import DataSeries

# Create your views here.

from django.http import HttpResponse

# We make the dictionary of data series forms
import PMD.forms

data_series_forms = dict()
for form in PMD.forms.__dict__.values():
	try:
		if form != PMD.forms.DataSeriesForm and issubclass(form, PMD.forms.DataSeriesForm):
			data_series_forms[form.base_fields["data_series"].initial] = form
	except Exception:
		pass

print data_series_forms

@login_required
def old_index(request):
	data_series_list = get_list_or_404(DataSeries)
	if not request.user.is_authenticated():
		print "User is not authenticated:"
	print request.user.username
	return render(request, 'PMD/index.html', {'data_series_list': data_series_list})

# Assert we only have post
@login_required
def bring_online(request):
	pass

# Assert we only have get
@login_required
def index(request):
	
	time_range_form = PMD.forms.TimeRangeForm()
	return render(request, 'PMD/search_data.html', {'time_range_form': time_range_form, 'data_series_forms': [form() for form in data_series_forms.values()]})

# Assert we only have get
@login_required
def search_data(request):
	time_range_form = PMD.forms.TimeRangeForm(request.GET)
	if time_range_form.is_valid():
		print time_range_form.cleaned_data['start_date']
		print time_range_form.cleaned_data['end_date']
		print time_range_form.cleaned_data['cadence']
		print time_range_form.cleaned_data['cadence_unit']
	else:
		print "time range invalid"
	data_series_form = data_series_forms[request.GET["data_series"]](request.GET)
	if data_series_form.is_valid():
		print 'best_quality' , data_series_form.cleaned_data['best_quality']
		# We return the requested data 
		#return HttpResponseRedirect('PMD/')
		return True
	else:
		# We need to return some error message
		return False
