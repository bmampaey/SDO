import os, errno
import subprocess
from datetime import datetime, timedelta
import logging
import pyfits
import math

def create_png(fits_file_name, image_file_name, parameters, executable = "fits2png.x", log = None):
	"""Call fits2png to convert a fits file to a png image
		parameters is a dictionary of arguments to pass to fits2png , see "fits2png -h" to get the possible values
	"""
	output_directory = os.path.dirname(image_file_name)
	if not output_directory:
		output_directory = "."
	
	# Create the directory tree for the image
	try:
		os.makedirs(output_directory)
	except OSError, why:
		if why.errno != errno.EEXIST:
			raise
	
	output_file = os.path.join(output_directory, os.path.splitext(os.path.basename(fits_file_name))[0] + "." + parameters.get("type", "png"))
	
	# Create the command
	command = [executable, fits_file_name, "-O", output_directory]
	for arg, value in parameters.iteritems():
		command.extend(["--%s" % arg, str(value)])
	if log:
		log.debug("Running command: ", " ".join(command))
	
	# Execute the command
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, error = process.communicate()
	if log:
		log.debug("Command \"%s\" output: %s; error: %s; returncode:%s", " ".join(command), output, error, process.returncode)
	if process.returncode !=0:
		raise Exception("Error running command %s. output: %s; error: %s; returncode:%s" % (" ".join(command), output, error, process.returncode))
	
	# Rename the output_file to image_file_name
	if output_file != image_file_name:
		os.rename(output_file, image_file_name)


def compare(record_set1, record_set2, compactness_flexibility = timedelta(seconds=10)):
	"""Compare 2 record set and return a positive value if the first is better, 0 if they are equal, and a negative value if the second is better"""
	
	# We check the set that is the most complete
	score = len(record_set1) - len(record_set2)
	if score != 0:
		logging.log(1, "Score from missing records : " + str(score) + ", set1 has " + str(len(record_set1)) + " set2 has " + str(len(record_set2)))
		return score
	
	# If they are similarly complete we check the one that has the best record quality
	common_channels = set(record_set1.keys()) & set(record_set2.keys())
	for channel in common_channels:
		score += cmp(record_set1[channel].quality, record_set2[channel].quality)
	
	if score != 0:
		logging.log(1, "Score from quality difference: " + str(score))
		return score
	
	# If they are similar in quality we check the one that is the most compact (we allow for 10 seconds of flexibility)
	record_set1_times = [record.date_obs for record in record_set1.itervalues()]
	delta_time_1 = max(record_set1_times) - min(record_set1_times)
	record_set2_times = [record.date_obs for record in record_set2.itervalues()]
	delta_time_2 = max(record_set2_times) - min(record_set2_times)
	if abs(delta_time_1 - delta_time_2) > compactness_flexibility:
		score = delta_time_2.total_seconds() - delta_time_1.total_seconds()
	
	logging.log(1, "Score from compactness difference: " + str(score) + ", set1 has " + str(delta_time_1) + " set2 has " + str(delta_time_2))
	return score


def create_record_sets(data_series_desc, frequency, start_date, end_date, compare = compare):
	
	slot_start = start_date
	slot_end = start_date + frequency
	
	record_sets = dict()
	while slot_end <= end_date:
		
		# Make the sorted list of all possible records for that time slot
		records = list()
		for desc, data_series in data_series_desc.iteritems():
			records.extend([(desc, record) for record in data_series.filter(date_obs__range=(slot_start, slot_end))])
		records.sort(key=lambda record: record[1].date_obs)
		
		# Create the best record set
		current_record_set = dict()
		best_record_set = dict()
		
		for desc, record in records:
			current_record_set[desc] = record
			# We update the best_record_set if the current_record_set is better
			if compare(current_record_set, best_record_set) > 0:
				best_record_set[desc] = record
		
		# Save the best record set for that time slot
		record_sets[slot_start] = best_record_set
		
		# Move the time slot
		slot_start = slot_end
		slot_end = slot_start + frequency
	
	return record_sets

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

