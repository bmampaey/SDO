def get_data_task(request):
	# get_local_file_path_task
	# get_data_location_task
	# data_download_task
	# get_data_task

def download_data_task(request):
	# pre_data_download
	# data_download
	# post_download_copy
	# update_fits_header_task

def get_data_location_task(request):
	# locate_data_task
	locate_data_task(request)
	# get_data_location_task

def locate_data_task(request):
	# locate_data

	# save_data_location

def delete_data_task(request):
	# get_local_file_path_task
	file_path = get_local_file_path_task(request)
	# delete_file
	delete_file(file_path)
	# delete_data_location
	delete_data_location(request)

def update_fits_header_task(request):
	# get_local_file_path_task
	file_path = get_local_file_path_task(request)
	if not file_path:
		raise Exception("Fits file for request %s is not available, download first" % request)

	# get_fits_header
	fits_header = get_fits_header(request)
	if not fits_header:
		raise Exception("No fits header for request %s " % request)

	# update_fits_header
 	update_fits_header(file_path, fits_header)


def get_local_file_path_task(request, check_file_exists = true):
	# search_local_file_path
	file_path = search_local_file_path(request)

	# check_file_exists (optional)
	if check_file_exists:
		if os.path.exists(file_path):
			return file_path
		else:
			return None
		else:
			return file_path


 def search_local_file_path(request):
		data_location_model.objects.get(data_series=request.data_series, recnum=request.recnum)
