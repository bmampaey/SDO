#!/usr/bin/python
import logging
import json
import signal
import threading
import Queue
import httplib
import urlparse
import os
import sys
import time
from django.db import IntegrityError
from get_config import get_config, update_config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

sys.path.append('/home/benjmam/SDO')
from PMD.models import DataSites, DataLocationQuery

# In the JMD, the len(sunums) < 100 et il chuffle les sunums si il y a error
def get_location(data_location_query_url, sunums, timeout = 120, max_attempts = 3, method = "GET"):
	'''Query a data site for the location of sunums'''
	
	# We parse the URL
	url_parts = urlparse.urlparse(data_location_query_url)
	if url_parts.scheme != "http" and url_parts.scheme != "":
		raise Exception("URL scheme is not http. URL was %s" % data_location_query_url)
	elif not url_parts.netloc:
		raise Exception("URL netloc not specified. URL was %s" % data_location_query_url)
	
	result = dict()
	if len(sunums) > 0:
		# We add the sunums to the URL
		sunums = [str(sunum) for sunum in sunums]
		sunums_query = "?op=exp_su&method=url_quick&format=json&formatvar=dataobj&protocol=as-is&requestid=NOASYNCREQUEST&sunum={sunums}".format(sunums=",".join(sunums))
		
		# We allow several attemps to get the response
		remaining_attempts = max_attempts
		response_content = None
		while remaining_attempts > 0 and response_content is None:
			try:
				# We try to get the http response
				connection = httplib.HTTPConnection(url_parts.netloc, timeout = timeout)
				connection.request(method, url_parts.path + sunums_query)
				response = connection.getresponse()
				if response.status != httplib.OK:
					raise Exception(response.reason)
				else:
					response_content = response.read()
			except Exception, why:
				# Something went wrong, we lost an attempt
				remaining_attempts -= 1
				logging.warning("Failed attempt %s/%s retrieving URL %s: %s.", max_attempts-remaining_attempts, max_attempts, data_location_query_url + sunums_query, str(why))
			finally:
				connection.close()
		
		
		if remaining_attempts == 0 or response_content is None: # We failed getting a response from the server
			raise Exception("Could not retrieve URL %s, %s failures. Last failure was %s." % (data_location_query_url + sunums_query, max_attempts, str(why)))
		
		else: # Success
			# We parse the json response to a dict
			try:
				response_json = json.loads(response_content)
			except Exception, why:
				raise Exception("Error parsing json from response to URL %s: %s. Response was: %s" % (data_location_query_url + sunums_query, str(why), response_content))
			
			if not "data" in response_json: # The response is not what we expected
				raise Exception("No data member available in response to URL %s. Response was: %s" % (data_location_query_url + sunums_query, response_content))
			
			data = response_json["data"]
			for sunum in sunums:
				if sunum in data:
					logging.debug("Found sunum %s in response: %s", sunum, data[sunum])
					result[int(sunum)] = data[sunum]
				else:
					logging.warning("Requested sunum %s not in response data: %s", sunum, data)
					result[int(sunum)] = None
	
	return result

#TODO check how to add path and size as a attribute of a query
def data_location_query_thread(query_queue, output_queue, data_site, delay = 5):
	'''Accumulate data location queries and call get_location to get the paths'''
	
	log = logging.getLogger(threading.current_thread().name)
	
	while True:
		queries = dict()
		sunums = list()
		total_priority = 0
		
		# We gather available queries until we have enough
		while total_priority < data_site.data_location_query_max_priority and len(sunums) < data_site.data_location_query_max_size and not query_queue.empty():
			query = query_queue.get() # We should never block because we just checked that the queue is not empty and are the only reader 
			sunums.append(query.sunum)
			total_priority += query.priority
			queries[query.sunum] = query
		
		if not sunums:
			logging.debug("No query available, sleeping for %s seconds", delay)
			time.sleep(delay)
			continue
		
		# We make the actual location query
		try:
			results = get_location(data_site.data_location_query_url, sunums, data_site.data_location_query_timeout, max_attempts = data_site.data_location_query_max_attempts)
		except Exception, why: # It failed :( We still return the queries but without the paths
			log.error(str(why))
			for query in queries.itervalues():
				query.path = None
				output_queue.put((query, None))
		else:
			# We update the queries with the path and the size
			for sunum, query in queries.iteritems():
				query.path = None
				query.size = 0
				if sunum not in results or results[sunum] is None:
					log.debug("No result found for sunum %s", sunum)
				else:
					result = results[sunum]
					if 'path' not in result or result['path'].upper() == "NA":
						log.debug("No path found for sunum %s", sunum)
					
					elif 'susize' not in result:
						# Because we don't know how to cope we just yell
						log.error("Path %s found for sunum %s, but susize not in result", result['path'], sunum)
					
					# Do we need those additional checks ?
					elif 'sustatus' in result and result['sustatus'].upper() != "Y":
						# Because we don't know how to cope we just yell
						log.error("Path %s found for sunum %s, but sustatus is %s", result['path'], sunum, result['sustatus'])
					
					elif 'sunum' in result and result['sunum'] != str(sunum):
						# Because we don't know how to cope we just yell
						log.error("Path %s found for sunum %s, but sunum in result %s is different than query sunum %s", result['path'], sunum, result['sunum'], query.sunum)
					
					elif 'series'in result and result['series'] != str(query.data_series):
						# Because we don't know how to cope we just yell
						log.error("Path %s found for sunum %s, but series in result %s is different than query data series %s", result['path'], sunum, result['series'], query.data_series)
					
					else:
						log.debug("Found path %s for sunum %s", result['path'], sunum)
						query.path = result['path']
						try:
							query.size = int(result['susize'])
						except Exception, why:
							log.error("Path %s found for sunum %s, but susize not an int", result['path'], sunum, result['susize'])
				
				# We send the updated query down the pipe
				output_queue.put(query) 

def manage_query_results(query_queue, output_queue):
	'''Update the data location tables with the results and forward them'''
	while True:
		query = query_queue.get()
		# Add the path to the data site table
		if query.path:
			data_location = query.data_site.data_location_model(data_series = query.data_series, sunum = query.sunum, slotnum = query.slotnum, path = query.path)
			logging.debug("Saving path for query %s to data location table of %s", unicode(query), query.data_site.name)
			try:
				data_location.save()
			except IntegrityError, why:
				logging.debug("Path for query %s was already in table, updating")
				data_location = query.data_site.data_location_model.objects.get(data_series = query.data_series, sunum = query.sunum, slotnum = query.slotnum)
				data_location.path = query.path
				data_location.save()
		
		# Remove the query from the table
		logging.debug("Deleting data location query %s from data base", unicode(query))
		query.delete()
		if output_queue:
			output_queue.put(query)


def data_location_query_manager(query_queue, output_queue):
	'''Dispatch the data location queries to the corresponding data_location_query_thread'''
	query_queues = dict()
	
	# data location queries have a lt operator defined so that higher priorities will be first
	threads_output_queue = Queue.PriorityQueue()
	
	# We start a thread to manage the output from the threads
	thread = threading.Thread(group=None, name="manage_query_results", target=manage_query_results, args=(threads_output_queue, output_queue))
	thread.daemon = True
	thread.start()
	
	# We wait for queries and dispatch them to the threads
	while True:
		query = query_queue.get()
		if query.data_site.name not in query_queues:
			# We start 1 thread for the data site
			query_queues[query.data_site.name] = Queue.PriorityQueue()
			logging.debug("Starting a new thread data_location_query_thread for data site %s", query.data_site.name)
			thread = threading.Thread(group=None, name="data_location_query for %s" % query.data_site.name, target=data_location_query_thread, args=(query_queues[query.data_site.name], threads_output_queue, data_sites[query.data_site.name]))
			thread.daemon = True
			thread.start()
		
		# We send the query to the good thread
		query_queues[query.data_site.name].put(query)

if __name__ == '__main__':
	
	logging.basicConfig(level=logging.INFO)
	
	# We setup the HUP signal so that it rereads the config when received
	signal.signal(signal.SIGHUP, update_config)
	data_series, data_sites, proactive_data_sites, local_data_site = get_config()
	
	query_queue = Queue.Queue()
	output_queue = Queue.PriorityQueue()
	thread = threading.Thread(group=None, name="data_location_query_manager", target=data_location_query_manager, args=(query_queue, output_queue))
	thread.daemon = True
	thread.start()
	number_queries = 0
	for data_location_query in DataLocationQuery.objects.all():
		query_queue.put(data_location_query)
		number_queries += 1
	
	while number_queries:
		query = output_queue.get()
		logging.info("Query %s with priority %s has been treated", query, query.priority)
		number_queries -= 1
	
	logging.info("Program has finished")
#	sunums = [547696328, 547696327, 547696326, 547696325, 547696324, 547696323, 547696322, 547696321, 547696320, 547696319, 547696318, 547696317, 547696316, 547696315, 547696314, 547696313, 547696312, 547696311, 547696309, 547696308, 547696307, 547696306, 547696305, 547696304, 547696292, 547696291, 547696290, 547696289, 547696288, 547696287, 547696286, 547696285, 547696282, 547696280, 547696273, 547696270, 547696284, 547696283, 547696281, 547696279, 547696278, 547696277, 547696276, 547696275, 547696274, 547696272, 547696271, 547696269, 547696120, 547696119, 547696118, 547696117, 547696116, 547696115, 547696114, 547696113, 547696112, 547696111, 547696110, 547696109, 547696102, 547696101, 547696100, 547696099, 547696098, 547696097, 547696094, 547696091, 547696090, 547696088, 547696086, 547696083, 547696096, 547696095, 547696093, 547696092, 547696089, 547696087, 547696085, 547696084, 547696082, 547696081, 547696080, 547696079, 547696072, 547696070, 547696067, 547696064, 547696060, 547696058, 547696056, 547696053, 547696051, 547696049, 547696043, 547696041, 547696071, 547696069, 547696066, 547696065, 547696062, 547696059, 547696054, 547696050, 547696048, 547696046, 547696045, 547696039, 547696068, 547696063, 547696061, 547696057, 547696055, 547696052, 547696047, 547696044, 547696042, 547696040, 547696038, 547696037, 547696034, 547696033, 547696032, 547696031, 547696030, 547696029, 547696027, 547696026, 547696025, 547696024, 547696022, 547696021, 547696023, 547696020, 547696017, 547696016, 547696015, 547696014, 547696013, 547696012, 547696011, 547696010, 547696009, 547696008, 547695918, 547695917, 547695916, 547695915, 547695914, 547695913, 547695912, 547695911, 547695910, 547695909, 547695908, 547695907, 547695878, 547695876, 547695875, 547695872, 547695869, 547695864, 547695862, 547695861, 547695858, 547695852, 547695815, 547695811, 547695873, 547695870, 547695868, 547695865, 547695863, 547695860, 547695855, 547695851, 547695848, 547695844, 547695841, 547695839, 547695743, 547695741, 547695737, 547695736, 547695734, 547695731, 547695726, 547695724, 547695723, 547695721, 547695717, 547695716, 547695740, 547695735, 547695733, 547695732, 547695730, 547695728, 547695727, 547695725, 547695720, 547695719, 547695718, 547695715, 547695712, 547695711, 547695710, 547695709, 547695707, 547695705, 547695704, 547695703, 547695702, 547695700, 547695698, 547695695, 547695701, 547695699, 547695697, 547695696, 547695694, 547695693, 547695691, 547695690, 547695689, 547695687, 547695686, 547695685, 547695682, 547695681, 547695680, 547695679, 547695678, 547695677, 547695676, 547695675, 547695674, 547695673, 547695672, 547695671, 547695346, 547695343, 547695342, 547695341, 547695340, 547695339, 547695337, 547695336, 547695335, 547695333, 547695332, 547695331, 547695270, 547695269, 547695267, 547695266, 547695265, 547695263, 547695262, 547695261, 547695260, 547695259, 547695257, 547695256, 547695226, 547695224, 547695223, 547695222, 547695218, 547695214, 547695212, 547695211, 547695207, 547695204, 547695201, 547695199, 547695220, 547695219, 547695217, 547695216, 547695215, 547695213, 547695210, 547695208, 547695206, 547695205, 547695203, 547695200, 547695175, 547695173, 547695171, 547695169, 547695168, 547695163, 547695157, 547695153, 547695146, 547695143, 547695136, 547695132, 547695174, 547695172, 547695165, 547695160, 547695158, 547695156, 547695150, 547695148, 547695140, 547695137, 547695133, 547695129, 547695170, 547695166, 547695164, 547695161, 547695155, 547695151, 547695145, 547695142, 547695139, 547695134, 547695130, 547695126, 547695167, 547695162, 547695159, 547695154, 547695149, 547695144, 547695141, 547695138, 547695135, 547695131, 547695128, 547695127, 547694894, 547694893, 547694892, 547694890, 547694886, 547694885, 547694884, 547694883, 547694882, 547694881, 547694880, 547694878, 547694728, 547694727, 547694726, 547694725, 547694724, 547694722, 547694721, 547694720, 547694718, 547694717, 547694716, 547694715, 547694608, 547694606, 547694605, 547694604, 547694603, 547694601, 547694597, 547694595, 547694591, 547694590, 547694589, 547694584, 547694602, 547694599, 547694596, 547694594, 547694593, 547694592, 547694588, 547694587, 547694585, 547694583, 547694582, 547694581, 547694563, 547694559, 547694554, 547694549, 547694543, 547694538, 547694535, 547694534, 547694531, 547694523, 547694522, 547694521, 547694566, 547694565, 547694564, 547694560, 547694558, 547694555, 547694550, 547694545, 547694540, 547694532, 547694530, 547694518, 547694561, 547694557, 547694556, 547694552, 547694547, 547694542, 547694537, 547694529, 547694528, 547694525, 547694517, 547694511, 547694553, 547694546, 547694544, 547694541, 547694539, 547694536, 547694533, 547694526, 547694524, 547694519, 547694515, 547694513, 547694242, 547694241, 547694240, 547694239, 547694238, 547694237, 547694236, 547694235, 547694234, 547694233, 547694232, 547694231, 547694177, 547694176, 547694175, 547694174, 547694173, 547694172, 547694171, 547694170, 547694168, 547694167, 547694165, 547694164, 547694137, 547694135, 547694133, 547694131, 547694128, 547694126, 547694125, 547694123, 547694121, 547694118, 547694116, 547694114, 547694136, 547694134, 547694132, 547694130, 547694127, 547694124, 547694120, 547694117, 547694115, 547694113, 547694111, 547694110, 547694075, 547694073, 547694070, 547694068, 547694063, 547694061, 547694057, 547694051, 547694046, 547694039, 547694037, 547694033, 547694078, 547694076, 547694074, 547694072, 547694062, 547694052, 547694049, 547694044, 547694043, 547694041, 547694038, 547694030, 547694067, 547694064, 547694059, 547694058, 547694055, 547694050, 547694048, 547694042, 547694040, 547694034, 547694031, 547694029, 547694066, 547694060, 547694053, 547694047, 547694045, 547694035, 547694032, 547694028, 547694026, 547694025, 547694024, 547694023, 547693681, 547693679, 547693678, 547693677, 547693676, 547693675, 547693674, 547693673, 547693672, 547693671, 547693669, 547693668, 547693523, 547693522, 547693521, 547693519, 547693518, 547693517, 547693516, 547693515, 547693514, 547693513, 547693511, 547693510, 547693466, 547693461, 547693459, 547693456, 547693451, 547693443, 547693437, 547693434, 547693433, 547693428, 547693424, 547693423, 547693460, 547693453, 547693452, 547693450, 547693446, 547693442, 547693441, 547693435, 547693431, 547693429, 547693425, 547693422, 547693419, 547693418, 547693417, 547693416, 547693415, 547693414, 547693413, 547693412, 547693411, 547693410, 547693409, 547693408, 547693339, 547693329, 547693311, 547693307, 547693299, 547693295, 547693289, 547693279, 547693277, 547693269, 547693266, 547693263, 547693351, 547693342, 547693334, 547693325, 547693321, 547693314, 547693304, 547693300, 547693275, 547693268, 547693259, 547693258, 547693310, 547693305, 547693301, 547693297, 547693288, 547693284, 547693281, 547693278, 547693274, 547693264, 547693260, 547693257, 547693080, 547693079, 547693078, 547693077, 547693076, 547693075, 547693074, 547693073, 547693072, 547693070, 547693068, 547693067, 547693008, 547693007, 547693005, 547693004, 547693003, 547693002, 547693001, 547693000, 547692999, 547692998, 547692996, 547692993, 547692966, 547692963, 547692961, 547692959, 547692956, 547692954, 547692945, 547692942, 547692938, 547692931, 547692924, 547692921, 547692962, 547692958, 547692953, 547692951, 547692950, 547692947, 547692944, 547692941, 547692936, 547692932, 547692927, 547692923, 547692960, 547692957, 547692955, 547692949, 547692948, 547692946, 547692940, 547692934, 547692929, 547692925, 547692920, 547692917, 547692943, 547692939, 547692937, 547692935, 547692933, 547692930, 547692926, 547692922, 547692919, 547692918, 547692916, 547692914, 547692878, 547692877, 547692875, 547692873, 547692870, 547692869, 547692867, 547692864, 547692861, 547692860, 547692858, 547692856, 547692876, 547692874, 547692872, 547692871, 547692868, 547692865, 547692863, 547692859, 547692857, 547692855, 547692854, 547692853, 547692521, 547692520, 547692519, 547692517, 547692516, 547692515, 547692514, 547692513, 547692510, 547692508, 547692506, 547692500, 547692490, 547692487, 547692485, 547692483, 547692482, 547692477, 547692476, 547692475, 547692472, 547692470, 547692468, 547692467, 547692491, 547692489, 547692488, 547692486, 547692484, 547692481, 547692480, 547692479, 547692474, 547692473, 547692469, 547692466, 547692384, 547692376, 547692365, 547692353, 547692349, 547692347, 547692345, 547692341, 547692339, 547692333, 547692329, 547692328, 547692350, 547692348, 547692344, 547692340, 547692338, 547692337, 547692335, 547692332, 547692327, 547692326, 547692324, 547692321, 547692352, 547692351, 547692346, 547692343, 547692342, 547692336, 547692334, 547692331, 547692330, 547692325, 547692323, 547692320, 547692297, 547692294, 547692292, 547692289, 547692287, 547692284, 547692281, 547692279, 547692276, 547692273, 547692272, 547692268, 547692295, 547692293, 547692291, 547692290, 547692288, 547692286, 547692285, 547692282, 547692278, 547692277, 547692274, 547692270, 547691996, 547691995, 547691994, 547691992, 547691990, 547691987, 547691985, 547691982, 547691979, 547691977, 547691974, 547691972, 547691989, 547691988, 547691986, 547691984, 547691983, 547691980, 547691978, 547691976, 547691975, 547691973, 547691970, 547691969, 547691942, 547691940, 547691937, 547691933, 547691931, 547691930, 547691928, 547691926, 547691924, 547691920, 547691919, 547691917, 547691943, 547691941, 547691939, 547691936, 547691934, 547691932, 547691929, 547691927, 547691925, 547691923, 547691918, 547691916, 547691890, 547691889, 547691888, 547691887, 547691886, 547691885, 547691883, 547691881, 547691879, 547691875, 547691873, 547691872, 547691882, 547691880, 547691878, 547691876, 547691874, 547691871, 547691870, 547691869, 547691868, 547691867, 547691866, 547691864, 547691865, 547691863, 547691862, 547691860, 547691858, 547691857, 547691855, 547691853, 547691852, 547691851, 547691850, 547691849, 547691824, 547691822, 547691820, 547691818, 547691817, 547691816, 547691814, 547691813, 547691812, 547691811, 547691809, 547691808, 547691446, 547691444, 547691442, 547691440, 547691438, 547691435, 547691433, 547691432, 547691430, 547691427, 547691424, 547691421, 547691443, 547691439, 547691437, 547691434, 547691431, 547691429, 547691426, 547691423, 547691420, 547691419, 547691415, 547691414, 547691355, 547691353, 547691352, 547691349, 547691348, 547691346, 547691343, 547691340, 547691338, 547691336, 547691334, 547691332, 547691347, 547691345, 547691344, 547691342, 547691341, 547691339, 547691337, 547691335, 547691333, 547691330, 547691329, 547691328, 547691277, 547691276, 547691275, 547691274, 547691273, 547691271, 547691268, 547691263, 547691261, 547691260, 547691258, 547691256, 547691272, 547691270, 547691266, 547691264, 547691259, 547691254, 547691253, 547691249, 547691247, 547691244, 547691243, 547691241, 547691269, 547691265, 547691262, 547691257, 547691255, 547691252, 547691251, 547691248, 547691246, 547691245, 547691242, 547691240, 547691216, 547691215, 547691213, 547691211]
#	sunums = [547696328, 547696327]
#	query_url = "http://sdo-db1.cfa.harvard.edu/cgi-bin/VSO/DRMS/vso_jsoc_fetch.cgi"
#	query_url = "http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_fetch_VSO"
#	logging.info("Requesting info at url %s for sunums %s", query_url, sunums)
#	try:
#		result = get_location(query_url, sunums, 10, 1)
#	except Exception, why:
#		logging.error(str(why))
#	else:
#		logging.info(str(result))
	
	



