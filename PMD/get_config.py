#!/usr/bin/python
import logging
import signal
import sys
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

sys.path.append('/home/benjmam/SDO')
import PMD.models

def get_config():
	'''Read the PMD config from database'''
	
	# Read the data series objects
	data_series = dict()
	for data_serie in PMD.models.DataSeries.objects.all():
		data_series[data_serie.name] = data_serie
	
	logging.debug("Found following data series: %s", data_series)
	
	# Read the data sites objects
	data_sites = dict()
	proactive_data_sites = list()
	local_data_site = None
	for data_site in PMD.models.DataSites.objects.all():
		data_sites[data_site.name] = data_site
		if data_site.local:
			if local_data_site is None:
				local_data_site = data_site
			else:
				raise Exception("Config error: more than one site is marked as local")
		elif data_site.proactively_query_location:
			proactive_data_sites.append(data_site)
	
	logging.debug("Found following data sites: %s", data_sites)
	logging.debug("Following data sites are pro-active: %s", proactive_data_sites)
	if local_data_site:
		logging.debug("Following data site is local: %s", local_data_site)
	else:
		logging.debug("Found no local data site")
	
	return data_series, data_sites, proactive_data_sites, local_data_site


def update_config(signal_number, stack_frame):
	'''Signal handler for the HUP signal'''
	global data_series, data_sites, proactive_data_sites, local_data_site
	logging.info("Updating config")
	data_series, data_sites, proactive_data_sites, local_data_site = get_config()


if __name__ == '__main__':
	
	logging.basicConfig(level=logging.DEBUG)
	
	# We setup the HUP signal so that it reread the config when received
	signal.signal(signal.SIGHUP, update_config)
	data_series, data_sites, proactive_data_sites, local_data_site = get_config()
	logging.info("Read following config:")
	logging.info("\tData series:\n\t%s", "\n\t".join([str(data_serie) for data_serie in data_series]))
	logging.info("\tData sites:\n\t%s", "\n\t".join([str(data_site) for data_site in data_sites]))
	
	while True:
		# We wait for a HUP signal
		signal.pause()
		logging.info("Read following config:")
		logging.info("\tData series:\n\t%s", "\n\t".join([str(data_serie) for data_serie in data_series]))
		logging.info("\tData sites:\n\t%s", "\n\t".join([str(data_site) for data_site in data_sites]))
