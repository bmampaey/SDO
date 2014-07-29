import json
from django.db import connection
from django.core.paginator import Paginator
import pprint

# See http://django-tastypie.readthedocs.org/en/latest/paginator.html why it is important for postgres to have a special paginator
class EstimatedCountPaginator(Paginator):
	
	def __init__(self, *args, **kwargs):
		count = kwargs.pop("count", None)
		max_estimate = kwargs.pop("max_estimate", 1000)
		super(EstimatedCountPaginator, self).__init__(*args, **kwargs)
		self._count = count
		self.max_estimate = max_estimate
	
	def _get_estimate_count(self):
		"""Returns an estimate of the total number of objects"""
		cursor = connection.cursor()
	
		# Postgres must be at least version 9
		if connection.connection.server_version < 90000:
			print "Postgres must be at least version 9.0, please upgrade."
			return 0
	
		# Remove limit and offset from the query, and extract sql and params.
		query = self.object_list.query
		query.low_mark = None
		query.high_mark = None
		query, params = self.object_list.query.sql_with_params()
	
		# Fetch the estimated rowcount from EXPLAIN json output.
		query = 'explain (format json) %s' % query
		cursor.execute(query, params)
		explain = cursor.fetchone()[0]
	
		# Older psycopg2 versions do not convert json automatically.
		if isinstance(explain, basestring):
			print "You should upgrade psycopg2"
			explain = json.loads(explain)
		print pprint.pformat(explain, depth=6)
		return explain[0]['Plan']['Plan Rows']
	
	@property
	def count(self):
		"""Return an estimate of the total number of objects if the estimate is greater than 1000"""
		if self._count is None:
			estimate = self._get_estimate_count()
			if estimate < self.max_estimate:
				self._count = self._get_count()
			else:
				self._count = estimate
		
		return self._count

class CadencePaginator(Paginator):
	def __init__(self, object_lists, cadence, per_page, orphans=0, allow_empty_first_page=True):
		self.object_lists = object_lists
		self.cadence = cadence
		# We cheat and actualy force the number of records per page to be a multiple of the number of objects lists 
		self._per_page = per_page
		self.orphans = int(orphans)
		self.allow_empty_first_page = allow_empty_first_page
		self._num_pages = self._count = None
		self._start_date = self._end_date = None
	
	@property
	def per_slot(self):
		return len(self.object_lists)
	
	@property
	def per_page(self):
		return max(int(self._per_page / self.per_slot) * self.per_slot, self.per_slot)
	
	@property
	def start_date(self):
		if self._start_date is None:
			self._start_date = min([object_list.order_by("date_obs").values("date_obs")[0]["date_obs"] for object_list in self.object_lists])
		return self._start_date
	
	@property
	def end_date(self):
		if self._end_date is None:
			self._end_date = max([object_list.order_by("-date_obs").values("date_obs")[0]["date_obs"] for object_list in self.object_lists])
		return self._end_date
	
	@property
	def count(self):
		if self._count is None:
			delta_time = self.end_date - self.start_date
			# The number of slots time the number per slots
			self._count = int(delta_time.total_seconds() / self.cadence.total_seconds()) * self.per_slot
		return self._count
	
	def page(self, number):
		number = self.validate_number(number)
		slot_start = self.start_date + (number - 1) * int(self.per_page / self.per_slot) * self.cadence
		
		# Make the list of objects for the page
		objects = list()
		
		# Avoid orphans
		if (number * self.per_page) + self.orphans >= self.count:
			while slot_start <= self.end_date:
				slot_end = slot_start + self.cadence
				objects.extend([object_list.filter(date_obs__range=(slot_start, slot_end)).order_by("date_obs")[0] for object_list in self.object_lists])
				slot_start = slot_end
		else:
			page_end = slot_start + int(self.per_page / self.per_slot) * self.cadence
			while slot_start < page_end:
				slot_end = slot_start + self.cadence
				objects.extend([object_list.filter(date_obs__range=(slot_start, slot_end)).order_by("date_obs")[0] for object_list in self.object_lists])
				slot_start = slot_end
		return self._get_page(objects, number, self)
