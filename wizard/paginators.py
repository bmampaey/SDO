from django.core.paginator import Paginator

class CadencePaginator(Paginator):
	"""Paginator that allows to specify a cadence. Relies on the date_obs attribute of the given object lists"""
	
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
		page_objects = list()
		#import pdb; pdb.set_trace()
		# Avoid orphans
		if (number * self.per_page) + self.orphans >= self.count:
			while slot_start <= self.end_date:
				slot_end = slot_start + self.cadence
				# For each object list, add the first one in the slot (if any)
				for object_list in self.object_lists:
					obj = object_list.order_by("date_obs").filter(date_obs__range=(slot_start, slot_end)).first()
					if obj:
						page_objects.append(obj)
				slot_start = slot_end
		else:
			page_end = slot_start + int(self.per_page / self.per_slot) * self.cadence
			while slot_start < page_end:
				slot_end = slot_start + self.cadence
				for object_list in self.object_lists:
					obj = object_list.order_by("date_obs").filter(date_obs__range=(slot_start, slot_end)).first()
					if obj:
						page_objects.append(obj)
				slot_start = slot_end
		return self._get_page(page_objects, number, self)
