import json
from django.db import connection
from django.core.paginator import Paginator
import pprint

class EstimatedCountPaginator(Paginator):

 def _get_estimate_count(self):
	"""Returns an estimate of the total number of objects"""
	cursor = connection.cursor()
	
	# Postgres must be at least version 9
	if connection.connection.server_version < 90000:
		print "Postgres must be at lesat version 9.0, please upgrade."
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
			if esimate < 1000:
				self._count = self.object_list.count()
			else:
				self._count = estimate
		
		return self._count
