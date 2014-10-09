from datetime import datetime, timedelta
import logging

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
		score += cmp(record_set1[channel], record_set2[channel])
	
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
	
	slot_start, slot_end  = start_date, start_date + frequency
	
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

import sys, os, errno


# This should go
sys.path.append('/home/benjmam/SDO')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings
from PMD.models import DataSeries
logging.basicConfig(level = logging.DEBUG)
def test_create_record_sets(frequency = timedelta(seconds=3600), start_date=datetime(2012,01,01), end_date = datetime(2012,01,02)):
	data_series_desc = dict()
	# For aia.lev1 it is 1 per wavelength
	aia_lev1 = DataSeries.objects.get(data_series__name="aia.lev1")
	
	for wavelength in [94, 131, 171, 193, 211, 304, 335, 1600, 1700, 4500]:
		data_series_desc["aia_lev1_%s" % wavelength] =  aia_lev1.model.objects.filter(wavelnth = wavelength, quality = 0)
	
	# We add hmi m45s and ic45s
	hmi_m_45s = DataSeries.objects.get(data_series__name="hmi.m_45s")
	data_series_desc["hmi_m_45s"] = hmi_m_45s.model.objects.filter(quality = 0)
	hmi_ic_45s = DataSeries.objects.get(data_series__name="hmi.ic_45s")
	data_series_desc["hmi_ic_45s"] = hmi_ic_45s.model.objects.filter(quality = 0)
	
	record_sets = create_record_sets(data_series_desc, frequency, start_date, end_date)
	for date, record_set in record_sets.iteritems():
		print date, record_set
