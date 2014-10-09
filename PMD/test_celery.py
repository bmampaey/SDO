from PMD.models import *
from PMD.tasks import *
meta_data = AiaLev1Record.objects.all()[1]
request = DataDownloadRequest.create_from_record(meta_data)
request.data_site = DataSite.objects.get(name = "JSOC")
get_data_location(request)
get_data_location.delay(request)
get_data(request)

meta_datas = list()
for dl in LocalDataLocation.objects.all():
	meta_datas.append(dl.data_series.record.objects.get(recnum=dl.recnum))


requests = [DataDownloadRequest.create_from_record(m) for m in meta_datas]

for r in requests:
	update_file_meta_data.delay(r)

import pyfits
paths = [dl.path for dl in LocalDataLocation.objects.all()]

for path in paths:
try:
hdus = pyfits.open(path)
hdus[1].data
except Exception, why:
print path, "is bas:", str(why)

