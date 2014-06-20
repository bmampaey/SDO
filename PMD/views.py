from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST

from PMD.models import DataSeries, DataDownloadRequest
import PMD.forms

from PMD.tasks import get_thumbnail, get_data, execute_bring_online_request, execute_export_data_request, execute_export_meta_data_request

import pprint

# We make the dictionary of data series forms
data_series_forms = dict()
for form in PMD.forms.__dict__.values():
	try:
		if form != PMD.forms.DataSeriesForm and issubclass(form, PMD.forms.DataSeriesForm):
			data_series_forms[form.record_table] = form
	except Exception:
		pass

print pprint.pformat(data_series_forms, depth=6)


# Assert we only have get
@require_safe
def index(request):
	context = {
		'time_range_form' : PMD.forms.TimeRangeForm(label_suffix=''),
		'data_series_forms': [data_series_forms[name](label_suffix='') for name in sorted(data_series_forms.keys())],
		'login_form': PMD.forms.LoginForm(label_suffix=''),
	}
	
	return render(request, 'PMD/search_data.html', context)

@require_POST
def login(request):
	form = PMD.forms.LoginForm(request.POST)
	if not form.is_valid():
		return HttpResponseBadRequest(str(form.errors))
	if form.cleaned_data["username"] and form.cleaned_data["password"]:
		user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
	elif form.cleaned_data["email"]:
		pass
	else:
		return HttpResponse("You must provide a username an password or an email", content_type="text/plain", status=401)
	if user is not None:
		if user.is_active:
			login(request, user)
			# Redirect to a success page.
		else:
			return HttpResponse("Your account is disabled. Please contact the website administrator", content_type="text/plain", status=401)
	else:
		return HttpResponse("Invalid password", content_type="text/plain", status=401)

# Assert we only have get
@require_safe
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


# Assert we only have get
@require_safe
def thumbnail(request, data_series, recnum):
	# Create the thumbnail request
	data_series_object = get_object_or_404(DataSeries, record_table=data_series)
	print "found", data_series
	record = get_object_or_404(data_series_object.record, recnum=recnum)
	thumbnail_request = DataDownloadRequest.create_from_record(record)

	# Execute the request
	try:
		path = get_thumbnail(thumbnail_request)
	except Exception, why:
		# In case of problem with the request return error message
		return HttpResponseServerError(str(why))
	else:
		# Redirect to the image
		return redirect(path, permanent=False)


# Assert we only have get
@require_safe
def download(request, data_series, recnum):
	# Create the thumbnail request
	data_series_object = get_object_or_404(DataSeries, record_table=data_series)
	print "found", data_series
	record = get_object_or_404(data_series_object.record, recnum=recnum)
	download_request = DataDownloadRequest.create_from_record(record)

	# Execute the request
	try:
		path = get_data(download_request)
	except Exception, why:
		# In case of problem with the request return error message
		return HttpResponseServerError(str(why))
	else:
		# Redirect to the image
		return redirect(path, permanent=False)


# Assert we only have post and that we are logged in
@require_POST
@login_required
def bring_online(request):
	if request.user.is_authenticated() and request.user.is_active:
		print request.user.username
	else:
		return HttpResponseForbidden("You are not allowed to do this")
