#!/usr/bin/python
import logging
import sys
import os
import argparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

sys.path.append('/home/benjmam/SDO')
from DRMS.models import DRMSDataSeries

def update_header(input_filename, output_filename, recnum = None, series_name = None):

hdus = pyfits.open(input_filename)
# Because SDO fits files do not follow the standard we need to fix them
hdus.verify('fix')

# There is a bug in the pyfits library, if it is a compressed hdu, you need the acces it's through the hidden header otherwise uptes are not written to files
header = hdus[1]._header

if series_name is None:
	if "SERIES" in header:
		series_name = header["SERIES"]
	else:
		logging.error("Series Name not provided and not in header")
		return

drms_data_series = DRMSDataSeries.objects.get(table = series_name)

if recnum is None:
	if "T_REC" in header and "WAVELNTH" in header:
		recnum = drms_data_series.objects.filter(t_rec = header["T_REC"], wavelnth = header["WAVELNTH"]).order_by('recnum')[0].recnum
	else:
		logging.error("Recnum not provided and missing T_REC and WAVELNTH in header")
		return

db_connection = psycopg2.connect(drmsdb_connection_string)
cursor = db_connection.cursor()

logging.debug("Getting units and comments for series %s", series_name)

print cursor.mogrify('select * from ' + units_comments[series_name])

cursor.execute('select * from ' + units_comments[series_name])

series_uc = dict()

for key, unit, comment in cursor:
	series_uc[key] = {'unit': unit, 'comment': comment}

print "Getting keywords for recnum", recnum

print cursor.mogrify('select * from ' + keywords[series_name] + ' where "RECNUM" = %(recnum)s', {'recnum' : recnum})

cursor.execute('select * from '+ keywords[series_name] + ' where "RECNUM" = %(recnum)s', {'recnum' : recnum})

values = cursor.fetchone()

# We free the db connection
db_connection.rollback()
db_connection.close()



for k, key in enumerate([column.name.upper() for column in cursor.description]):
	value = values[k]
	# Some values are non conform to the fits standard so we need to modify them
	if type(value) == datetime:
		if series_uc[key]['unit'] == "TAI":
			value = value.strftime("%Y-%m-%dT%H:%M:%S.%f_TAI")
		else:
			value = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
	elif type(value) is float:
		if math.isnan(value):
			value = "nan"
		elif math.isinf(value):
			value = "inf"
	# We compose the comment
	comment = ""
	if key in series_uc:
		if series_uc[key]['unit'] is not None:
			comment += "[" + series_uc[key]['unit'] + "] "
		if series_uc[key]['comment'] is not None:
			comment += series_uc[key]['comment']
	# We update the keyword
	if comment:
		header[key] = (value, comment)
	else:
		header[key] = value
	print key, "=", header[key]

hdus.writeto(outfilename, clobber=True, checksum=True)


if __name__ == '__main__':
	
	logging.basicConfig(level=logging.DEBUG)
	parser = argparse.ArgumentParser(description='Update the header of a SDO fits file')
	parser.add_argument('input_fits_file', help='The fits file to update')
	parser.add_argument('output_fits_file', nargs='?', help='A optional name for the output fits file')
	parser.add_argument('--series', help='The data series name')
	parser.add_argument('--recnum', type=int, help='The recnum')
	
	args = parser.parse_args()
	if args.output_fits_file:
		outfilename = sys.argv[4]
	else:
		outfilename = filename

