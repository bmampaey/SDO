from datetime import datetime
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from tasks import create_AIA_HMI_synoptic_tree



class Command(BaseCommand):
	help = 'Create a AIA HMI synoptic tree'
	option_list = BaseCommand.option_list + (
		make_option(
			'-c', '--config',
			dest = 'config',
			default = 'AIA_HMI_1H_synoptic',
			help = 'Prefix for the global variable'
		),
		make_option(
			'-s', '--start_date',
			dest = 'start_date',
			default = '2010-05-13',
			help = 'Start date of the tree'
		),
		make_option(
			'-e', '--end_date',
			dest = 'end_date',
			default = datetime.today().strftime('%Y-%m-%d'),
			help = 'End date of the tree'
		),
		make_option(
			'-f', '--folder',
			dest = 'folder',
			default = '/data/public/AIA_HMI_1h_synoptic/',
			help = 'Folder where to create the tree'
		)
	)
	
	def handle(self, *args, **options):
		self.stdout.write('options %s' % options)
		start_date = datetime.strptime(options['start_date'], '%Y-%m-%d')
		end_date = datetime.strptime(options['end_date'], '%Y-%m-%d')
		create_AIA_HMI_synoptic_tree(options['config'], start_date = start_date, end_date = end_date, root_folder = options['folder'])
