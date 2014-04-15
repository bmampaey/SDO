from __future__ import absolute_import
import sys
from celery import Celery

sys.path.append('/home/benjmam/SDO')
PMD_app = Celery('PMD_app', broker='amqp://', backend='amqp://', include=['PMD.daemon.celery_tasks'])

# Optional configuration, see the application user guide.
PMD_app.conf.update(
	CELERY_TASK_RESULT_EXPIRES=3600,
	CELERY_DISABLE_RATE_LIMITS = True, # To be removed if we set a rate limit on some tasks
)

if __name__ == '__main__':
	PMD_app.start()
