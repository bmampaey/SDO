import json
import pprint
from django.db import connection
from django.core.paginator import Paginator as DjangoPaginator
from tastypie.paginator import Paginator as TastypiePaginator

# See http://django-tastypie.readthedocs.org/en/latest/paginator.html why it is important for postgres to have a special paginator

class EstimatedCountPaginator(DjangoPaginator):
	
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
		query.low_mark = 0
		query.high_mark = None
		query_str, params = query.sql_with_params()
	
		# Fetch the estimated rowcount from EXPLAIN json output.
		query_str = 'explain (format json) ' + query_str
		try:
			cursor.execute(query_str, params)
			explain = cursor.fetchone()[0]
		except Exception, why:
			return self._get_count()
	
		# Older psycopg2 versions do not convert json automatically.
		if isinstance(explain, basestring):
			print "You should upgrade psycopg2"
			explain = json.loads(explain)
		# print pprint.pformat(explain, depth=6)
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

class TastypieEstimatedCountPaginator(TastypiePaginator):

	def get_next(self, limit, offset, count):
		# The parent method needs an int which is higher than "limit + offset"
		# to return a url. Setting it to an unreasonably large value, so that
		# the parent method will always return the url.
		count = 2 ** 64
		return super(EstimatedCountPaginator, self).get_next(limit, offset, count)

	def get_count(self):
		return None

	def get_estimated_count(self):
		"""Get the estimated count by using the database query planner."""
		# If you do not have PostgreSQL as your DB backend, alter this method
		# accordingly.
		return self._get_postgres_estimated_count()

	def _get_postgres_estimated_count(self):

		# This method only works with postgres >= 9.0.
		# If you need postgres vesrions less than 9.0, remove "(format json)"
		# below and parse the text explain output.

		def _get_postgres_version():
			# Due to django connections being lazy, we need a cursor to make
			# sure the connection.connection attribute is not None.
			connection.cursor()
			return connection.connection.server_version
		
		try:
			if _get_postgres_version() < 90000:
				print "Postgres version too low for the EstimatedCountPaginator:",  _get_postgres_version()
				return
		except AttributeError:
			return
		
		cursor = connection.cursor()
		query = self.objects.all().query
		
		# Remove limit and offset from the query, and extract sql and params.
		query.low_mark = 0
		query.high_mark = None
		query_str, params = self.objects.query.sql_with_params()
		
		# Fetch the estimated rowcount from EXPLAIN json output.
		query_str = 'explain (format json) ' + query_str
		try:
			cursor.execute(query_str, params)
			explain = cursor.fetchone()[0]
		except Exception, why:
			return self._get_count()
		
		# Older psycopg2 versions do not convert json automatically.
		if isinstance(explain, basestring):
			explain = json.loads(explain)
		rows = explain[0]['Plan']['Plan Rows']
		return rows
		
	def page(self):
		data = super(EstimatedCountPaginator, self).page()
		data['meta']['estimated_count'] = self.get_estimated_count()
		return data
