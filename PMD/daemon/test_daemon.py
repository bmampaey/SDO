#!/usr/bin/python
from celery_tasks import get_data_location_tasks, save_data_location_tasks
from request import DataLocationRequest, DownloadRequest

data_location_requests = [
	DataLocationRequest('JSOC', 'aia.lev1', 547696328, segment = "aia.lev1"),
	DataLocationRequest('JSOC', 'hmi.ic_45s', 547696327)
]

data_location_request = data_location_requests[0]
req = get_data_location_tasks[data_location_request.data_site_name].apply_async([data_location_request], link=save_data_location_tasks[data_location_request.data_site_name].s(), link_error=save_data_location_tasks[data_location_request.data_site_name].s())

requests = dict()
for data_location_request in data_location_requests:
	if data_location_request.data_site_name in get_data_location_tasks:
		requests[data_location_request] = get_data_location_tasks[data_location_request.data_site_name].delay(data_location_request)
	else:
		print "No"

#	req[sunum] = (get_data_location_tasks['ROB'].s(sunum)|save_data_location_tasks['ROB'].s())()

for data_location_request, request in requests.iteritems():
	request.wait(propagate=False)
	print data_location_request, request.status, request.result
	if request.successful():
		print request.result.path
		requests[data_location_request] = save_data_location_tasks[data_location_request.data_site_name].delay(request.result)
	else:
		requests[data_location_request] = None


for data_location_request, request in requests.iteritems():
	if request:
		request.wait(propagate=False)
		print data_location_request, request.status, request.result
