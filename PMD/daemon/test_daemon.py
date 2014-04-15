#!/usr/bin/python
from celery_tasks import get_data_location_tasks, save_data_location_tasks
from request import DataLocationRequest, DownloadRequest

data_location_requests = [
	DataLocationRequest('JSOC', 'aia.lev1', 547696328),
	DataLocationRequest('ROB', 'aia.lev1', 547696327)
]

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
