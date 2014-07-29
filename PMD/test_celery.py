from PMD.models import *
from PMD.tasks import *
meta_data = AiaLev1Record.objects.all()[1]
request = DataDownloadRequest.create_from_record(meta_data)
request.data_site = DataSite.objects.get(name = "JSOC")
get_data_location(request)
get_data_location.delay(request)
get_data(request)

