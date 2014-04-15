from datetime import datetime

class DownloadRequest:
	def __init__(self, data_series_name, sunum, slotnum, segment, priority = 0, status = "NEW", request_date = datetime.now(), update_date = datetime.now()):
		self.data_series_name = data_series_name
		self.sunum = sunum
		self.slotnum = slotnum
		self.segment = segment
		self.priority = priority
		self.status = status
		self.request_date = request_date
		self.update_date = update_date
	
	def __str__(self):
		return "%s D%d/S%06d %s" % (self.data_series_name, self.sunum, self.slotnum, self.status)
	
	def __repr__(self):
		return "%s D%d/S%06d %s" % (self.data_series_name, self.sunum, self.slotnum, self.status)
		
	def __lt__(self, other):
		'''Return true if the priority is bigger'''
		if self.priority > other.priority:
			return True
		elif self.priority == other.priority:
			return self.requeste_date < other.requeste_date
		else:
			return False


class DataLocationRequest:
	def __init__(self, data_site_name, data_series_name, sunum, slotnum = 0, segment = None, recnum = None, priority = 0, status = "NEW", request_date = datetime.now(), update_date = datetime.now()):
		self.data_site_name = data_site_name
		self.data_series_name = data_series_name
		self.sunum = sunum
		self.slotnum = slotnum
		self.segment = segment
		self.recnum = recnum
		self.priority = priority
		self.status = status
		self.request_date = request_date
		self.update_date = update_date
		self.path = None
		self.size = None
	
	def __str__(self):
		return "%s D%d/S%06d %s" % (self.data_series_name, self.sunum, self.slotnum, self.status)
	
	def __repr__(self):
		return "%s D%d/S%06d %s" % (self.data_series_name, self.sunum, self.slotnum, self.status)
		
	def __lt__(self, other):
		'''Return true if the priority is bigger'''
		if self.priority > other.priority:
			return True
		elif self.priority == other.priority:
			return self.requeste_date < other.requeste_date
		else:
			return False



