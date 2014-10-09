import pyfits
import math
from datetime import datetime
import logging


def update_fits_header(file_path, header_values, header_comments, header_units, out_file_path = None, hdu = 0, log = logging):
	"""Update the fits header of a file"""
	
	if out_file_path is None or file_path == out_file_path:
		hdus = pyfits.open(file_path, mode="update")
	else:
		hdus = pyfits.open(file_path)
	
	# SDO fits files are often erronous, so we need to fix them first to use them
	hdus.verify('silentfix')
	
	# Because of a bug in the pyfits library, if we have a compressed image we need to update the hidden header
	if type(hdus[hdu]) == pyfits.CompImageHDU:
		header = hdus[hdu]._header
	else:
		header = hdus[hdu].header
	
	for keyword, value in header_values.items():
		
		# Some values are non conform to the fits standard so we need to modify them
		if type(value) == datetime:
			if keyword in header_units and header_units[keyword] == "TAI":
				value = value.strftime("%Y-%m-%dT%H:%M:%S.%f_TAI")
			else:
				value = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
		elif type(value) is float:
			if math.isnan(value):
				value = "nan"
			elif math.isinf(value):
				value = "inf"
		
		# We compose the keyword comment
		comment = ""
		if keyword in header_units and header_units[keyword]:
			comment += "[" + header_units[keyword] + "] "
		if keyword in header_comments and header_comments[keyword]:
			comment += header_comments[keyword]
		
		# We update the keyword
		if comment:
			header[keyword] = (value, comment)
		else:
			header[keyword] = value
		
		log.debug("Update keyword %s to %s, %s", keyword, value, comment)
		
	if out_file_path is None or file_path == out_file_path:
		hdus.close(output_verify="silentfix")
	else:
		hdus.writeto(file_path, output_verify='silentfix', clobber=True, checksum=True)

