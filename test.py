#!/usr/bin/python
import logging
import signal
import sys
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SDO.settings")
from django.conf import settings

sys.path.append('/home/benjmam/SDO')
from DRMS.models import DRMSDataSeries

o = DRMSDataSeries.objects.all()[0]
print o.fits_units_comments_model.objects.all()
