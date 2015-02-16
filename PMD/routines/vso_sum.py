import subprocess
import logging
from datetime import datetime, timedelta

def call_vso_sum_alloc(data_series_name, sunum, size, vso_sum_alloc = "vso_sum_alloc", log = logging):
	"""Call vso_sum_alloc to get a directory from sum_svc"""
	
	command = [vso_sum_alloc, "sunum=%s"%sunum, "size=%s"%size, "seriesname=%s"%data_series_name]
	log.debug("Running command: ", " ".join(command))
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, error = process.communicate()
	log.debug("Command \"%s\" output: %s; error: %s; returncode:%s", " ".join(command), output, error, process.returncode)
	if process.returncode !=0:
		raise Exception("Error running command %s. output: %s; error: %s; returncode:%s" % (" ".join(command), output, error, process.returncode))
	
	# Extract the directory from the output
	sudir = None
	for part in output.split(';'):
		subparts = part.split(':')
		if subparts[0].lower() == "sudir" and len(subparts) >= 2:
			sudir = subparts[1].strip()
			break
	if not sudir:
		raise Exception("Error running vso_sum_alloc for %s %s :%s" % (data_series_name, sunum, output))
	
	log.debug("vso_sum_alloc sudir for %s %s : %s", data_series_name, sunum, sudir)
	
	return sudir


def call_vso_sum_put(data_series_name, sunum, sudir, retention, vso_sum_put = "vso_sum_put", log = logging):
	"""Call vso_sum_put to register a sudir to sum_svc"""
	
	command = [vso_sum_put, "sunum=%s"%sunum, "seriesname=%s"%data_series_name, "sudir=%s"%sudir, "retention=%s"%retention]
	log.debug("Running command: ", " ".join(command))
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, error = process.communicate()
	log.debug("Command \"%s\" output: %s; error: %s; returncode:%s", " ".join(command), output, error, process.returncode)
	if process.returncode !=0:
		raise Exception("Error running command %s. output: %s; error: %s; returncode:%s" % (" ".join(command), output, error, process.returncode))
	
	return sudir

