from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST

from PMD.models import DataSeries, DataDownloadRequest
from PMD.forms import TimeRangeForm, LoginForm, DataSeriesSearchForm
from PMD.tasks import get_preview, get_data, execute_bring_online_request, execute_export_data_request, execute_export_meta_data_request

# Assert we only have get
@require_safe
def index(request):
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	context = {
		'time_range_form' : TimeRangeForm(label_suffix=''),
		'data_series_search_forms': [data_series_search_forms[name](label_suffix='') for name in sorted(data_series_search_forms)],
		'login_form': LoginForm(label_suffix=''),
	}
	
	return render(request, 'PMD/index.html', context)

# Assert we only have get
@require_safe
def result_table(request, data_series_name):
	#import pprint; print pprint.pformat(request.GET, depth=6)
	#import pdb; pdb.set_trace()
	# Get the request session for the requested data series
	if data_series_name not in request.session:
		request.session[data_series_name] = dict()
	request_session = request.session[data_series_name]
	
	# Update the request session
	request_session["search_id"] = request.GET.get("search_id", request_session.get("search_id", None))
	
	# Get the result table
	data_series_search_forms = DataSeriesSearchForm.sub_forms()
	if data_series_name in data_series_search_forms:
		try:
			result_table = data_series_search_forms[data_series_name].get_result_table(request.GET, request_session, request.GET.get('page', 1))
		except Exception, why:
			return HttpResponseBadRequest(str(why))
	else:
		return HttpResponseBadRequest("Unknown data series %s" % data_series_name)
	
	result_table["search_id"] = request_session["search_id"]
	return render(request, 'PMD/result_table.html', result_table)

@require_POST
def login(request):
	form = LoginForm(request.POST)
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
def preview(request, data_series_name, recnum):
	# Create the preview request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	preview_request = DataDownloadRequest.create_from_record(record)

	# Execute the request
	try:
		path = get_preview(preview_request)
	except Exception, why:
		# In case of problem with the request return error message
		print why
		return HttpResponseServerError(str(why))
	else:
		# Redirect to the image
		return redirect(path, permanent=False)


# Assert we only have get
@require_safe
def download(request, data_series_name, recnum):
	# Create the preview request
	data_series = get_object_or_404(DataSeries, pk=data_series_name)
	print "found", data_series_name
	record = get_object_or_404(data_series.record, recnum=recnum)
	download_request = DataDownloadRequest.create_from_record(record)
	
	# Execute the request
	try:
		path = get_data(download_request)
	except Exception, why:
		# In case of problem with the request return error message
		return HttpResponseServerError(str(why))
	else:
		# Send the file
		response = HttpResponse(open(path,"rb").read(), mimetype="application/x-download")
		response["Content-Disposition"] = "attachment;filename="+record.filename()
		return response


# Assert we only have post and that we are logged in
@require_POST
@login_required
def download_bundle(request, data_series_name):
	pass

# Assert we only have post and that we are logged in
@require_POST
@login_required
def export_data(request, data_series_name):
	pass

# Assert we only have post and that we are logged in
@require_POST
@login_required
def export_keywords(request, data_series_name):
	pass


# Assert we only have post and that we are logged in
@require_POST
@login_required
def bring_online(request, data_series_name):
	if request.user.is_authenticated() and request.user.is_active:
		print request.user.username
	else:
		return HttpResponseForbidden("You are not allowed to do this")

# Assert we only have post and that we are logged in
@require_POST
@login_required
def export_cutout(request, data_series_name):
	pass

