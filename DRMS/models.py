# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines for those models you wish to give write DB access
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models
import django.db.models.options as options

# This allow us to add a fully_qualified_db_table filed to teh mata class
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('fully_qualified_db_table',)


class DRMSDataSeries(models.Model):
	name = models.CharField("Data series name", help_text = "Meta-data database table of the data series. Must be fully qualified.", max_length=20, primary_key = True)
	fits_header_view = models.CharField(help_text = "View to retrieve fits header for the data series.", max_length=50)
	fits_keyword_view = models.CharField(help_text = "View to retrieve fits keywords, units and comments for the data series.", max_length=50)
	
	class Meta:
		db_table = "drms_data_series"
		verbose_name = "Data series"
		verbose_name_plural = "Data series"
	
	def __unicode__(self):
		return unicode(self.name)
	
	def __set_models(self):
		import DRMS.models as DRMS_models
		for model_name in dir(DRMS_models):
			try:
				DRMS_model = getattr(DRMS_models, model_name)
				if DRMS_model._meta.db_table == self.fits_header_view:
					self.__fits_header_model = DRMS_model
				elif DRMS_model._meta.db_table == self.fits_keyword_view:
					self.__fits_keyword_model = DRMS_model
				elif DRMS_model._meta.fully_qualified_db_table == self.name:
					self.__drms_model = DRMS_model
			except Exception:
				pass
	
	@property
	def drms_model(self):
		if not hasattr(self, '__drms_model'):
			self.__set_models()
		return self.__drms_model
	
	@property
	def fits_header_model(self):
		if not hasattr(self, '__fits_header_model'):
			self.__set_models()
		return self.__fits_header_model
	
	@property
	def fits_keyword_model(self):
		if not hasattr(self, '__fits_keyword_model'):
			self.__set_models()
		return self.__fits_keyword_model

# Field names are lowercase.
class AiaLev1FitsHeader(models.Model):
	bld_vers = models.TextField(db_column='BLD_VERS', blank=True)
	lvl_num = models.FloatField(db_column='LVL_NUM', blank=True, null=True)
	t_rec = models.DateTimeField(db_column='T_REC', blank=True, null=True)
	origin = models.TextField(db_column='ORIGIN', blank=True)
	date = models.DateTimeField(db_column='DATE', blank=True, null=True)
	telescop = models.TextField(db_column='TELESCOP', blank=True)
	instrume = models.TextField(db_column='INSTRUME', blank=True)
	date_obs = models.DateTimeField(db_column='DATE-OBS', blank=True, null=True)
	t_obs = models.DateTimeField(db_column='T_OBS', blank=True, null=True)
	camera = models.IntegerField(db_column='CAMERA', blank=True, null=True)
	img_type = models.TextField(db_column='IMG_TYPE', blank=True)
	exptime = models.FloatField(db_column='EXPTIME', blank=True, null=True)
	expsdev = models.FloatField(db_column='EXPSDEV', blank=True, null=True)
	int_time = models.FloatField(db_column='INT_TIME', blank=True, null=True)
	wavelnth = models.IntegerField(db_column='WAVELNTH', blank=True, null=True)
	waveunit = models.TextField(db_column='WAVEUNIT', blank=True)
	wave_str = models.TextField(db_column='WAVE_STR', blank=True)
	fsn = models.IntegerField(db_column='FSN', blank=True, null=True)
	fid = models.IntegerField(db_column='FID', blank=True, null=True)
	quallev0 = models.IntegerField(db_column='QUALLEV0', blank=True, null=True)
	quality = models.IntegerField(db_column='QUALITY', blank=True, null=True)
	totvals = models.IntegerField(db_column='TOTVALS', blank=True, null=True)
	datavals = models.IntegerField(db_column='DATAVALS', blank=True, null=True)
	missvals = models.IntegerField(db_column='MISSVALS', blank=True, null=True)
	percentd = models.FloatField(db_column='PERCENTD', blank=True, null=True)
	datamin = models.IntegerField(db_column='DATAMIN', blank=True, null=True)
	datamax = models.IntegerField(db_column='DATAMAX', blank=True, null=True)
	datamedn = models.IntegerField(db_column='DATAMEDN', blank=True, null=True)
	datamean = models.FloatField(db_column='DATAMEAN', blank=True, null=True)
	datarms = models.FloatField(db_column='DATARMS', blank=True, null=True)
	dataskew = models.FloatField(db_column='DATASKEW', blank=True, null=True)
	datakurt = models.FloatField(db_column='DATAKURT', blank=True, null=True)
	datacent = models.FloatField(db_column='DATACENT', blank=True, null=True)
	datap01 = models.FloatField(db_column='DATAP01', blank=True, null=True)
	datap10 = models.FloatField(db_column='DATAP10', blank=True, null=True)
	datap25 = models.FloatField(db_column='DATAP25', blank=True, null=True)
	datap75 = models.FloatField(db_column='DATAP75', blank=True, null=True)
	datap90 = models.FloatField(db_column='DATAP90', blank=True, null=True)
	datap95 = models.FloatField(db_column='DATAP95', blank=True, null=True)
	datap98 = models.FloatField(db_column='DATAP98', blank=True, null=True)
	datap99 = models.FloatField(db_column='DATAP99', blank=True, null=True)
	nsatpix = models.IntegerField(db_column='NSATPIX', blank=True, null=True)
	oscnmean = models.FloatField(db_column='OSCNMEAN', blank=True, null=True)
	oscnrms = models.FloatField(db_column='OSCNRMS', blank=True, null=True)
	flat_rec = models.TextField(db_column='FLAT_REC', blank=True)
	nspikes = models.IntegerField(db_column='NSPIKES', blank=True, null=True)
	ctype1 = models.TextField(db_column='CTYPE1', blank=True)
	cunit1 = models.TextField(db_column='CUNIT1', blank=True)
	crval1 = models.FloatField(db_column='CRVAL1', blank=True, null=True)
	cdelt1 = models.FloatField(db_column='CDELT1', blank=True, null=True)
	crpix1 = models.FloatField(db_column='CRPIX1', blank=True, null=True)
	ctype2 = models.TextField(db_column='CTYPE2', blank=True)
	cunit2 = models.TextField(db_column='CUNIT2', blank=True)
	crval2 = models.FloatField(db_column='CRVAL2', blank=True, null=True)
	cdelt2 = models.FloatField(db_column='CDELT2', blank=True, null=True)
	crpix2 = models.FloatField(db_column='CRPIX2', blank=True, null=True)
	crota2 = models.FloatField(db_column='CROTA2', blank=True, null=True)
	r_sun = models.FloatField(db_column='R_SUN', blank=True, null=True)
	mpo_rec = models.TextField(db_column='MPO_REC', blank=True)
	inst_rot = models.FloatField(db_column='INST_ROT', blank=True, null=True)
	imscl_mp = models.FloatField(db_column='IMSCL_MP', blank=True, null=True)
	x0_mp = models.FloatField(db_column='X0_MP', blank=True, null=True)
	y0_mp = models.FloatField(db_column='Y0_MP', blank=True, null=True)
	asd_rec = models.TextField(db_column='ASD_REC', blank=True)
	sat_y0 = models.FloatField(db_column='SAT_Y0', blank=True, null=True)
	sat_z0 = models.FloatField(db_column='SAT_Z0', blank=True, null=True)
	sat_rot = models.FloatField(db_column='SAT_ROT', blank=True, null=True)
	acs_mode = models.TextField(db_column='ACS_MODE', blank=True)
	acs_eclp = models.TextField(db_column='ACS_ECLP', blank=True)
	acs_sunp = models.TextField(db_column='ACS_SUNP', blank=True)
	acs_safe = models.TextField(db_column='ACS_SAFE', blank=True)
	acs_cgt = models.TextField(db_column='ACS_CGT', blank=True)
	orb_rec = models.TextField(db_column='ORB_REC', blank=True)
	dsun_ref = models.FloatField(db_column='DSUN_REF', blank=True, null=True)
	dsun_obs = models.FloatField(db_column='DSUN_OBS', blank=True, null=True)
	rsun_ref = models.FloatField(db_column='RSUN_REF', blank=True, null=True)
	rsun_obs = models.FloatField(db_column='RSUN_OBS', blank=True, null=True)
	gaex_obs = models.FloatField(db_column='GAEX_OBS', blank=True, null=True)
	gaey_obs = models.FloatField(db_column='GAEY_OBS', blank=True, null=True)
	gaez_obs = models.FloatField(db_column='GAEZ_OBS', blank=True, null=True)
	haex_obs = models.FloatField(db_column='HAEX_OBS', blank=True, null=True)
	haey_obs = models.FloatField(db_column='HAEY_OBS', blank=True, null=True)
	haez_obs = models.FloatField(db_column='HAEZ_OBS', blank=True, null=True)
	obs_vr = models.FloatField(db_column='OBS_VR', blank=True, null=True)
	obs_vw = models.FloatField(db_column='OBS_VW', blank=True, null=True)
	obs_vn = models.FloatField(db_column='OBS_VN', blank=True, null=True)
	crln_obs = models.FloatField(db_column='CRLN_OBS', blank=True, null=True)
	crlt_obs = models.FloatField(db_column='CRLT_OBS', blank=True, null=True)
	car_rot = models.IntegerField(db_column='CAR_ROT', blank=True, null=True)
	hgln_obs = models.FloatField(db_column='HGLN_OBS', blank=True, null=True)
	hglt_obs = models.FloatField(db_column='HGLT_OBS', blank=True, null=True)
	roi_nwin = models.IntegerField(db_column='ROI_NWIN', blank=True, null=True)
	roi_sum = models.IntegerField(db_column='ROI_SUM', blank=True, null=True)
	roi_nax1 = models.IntegerField(db_column='ROI_NAX1', blank=True, null=True)
	roi_nay1 = models.IntegerField(db_column='ROI_NAY1', blank=True, null=True)
	roi_llx1 = models.IntegerField(db_column='ROI_LLX1', blank=True, null=True)
	roi_lly1 = models.IntegerField(db_column='ROI_LLY1', blank=True, null=True)
	roi_nax2 = models.IntegerField(db_column='ROI_NAX2', blank=True, null=True)
	roi_nay2 = models.IntegerField(db_column='ROI_NAY2', blank=True, null=True)
	roi_llx2 = models.IntegerField(db_column='ROI_LLX2', blank=True, null=True)
	roi_lly2 = models.IntegerField(db_column='ROI_LLY2', blank=True, null=True)
	pixlunit = models.TextField(db_column='PIXLUNIT', blank=True)
	dn_gain = models.FloatField(db_column='DN_GAIN', blank=True, null=True)
	eff_area = models.FloatField(db_column='EFF_AREA', blank=True, null=True)
	eff_ar_v = models.FloatField(db_column='EFF_AR_V', blank=True, null=True)
	tempccd = models.FloatField(db_column='TEMPCCD', blank=True, null=True)
	tempgt = models.FloatField(db_column='TEMPGT', blank=True, null=True)
	tempsmir = models.FloatField(db_column='TEMPSMIR', blank=True, null=True)
	tempfpad = models.FloatField(db_column='TEMPFPAD', blank=True, null=True)
	ispsname = models.TextField(db_column='ISPSNAME', blank=True)
	isppktim = models.DateTimeField(db_column='ISPPKTIM', blank=True, null=True)
	isppktvn = models.TextField(db_column='ISPPKTVN', blank=True)
	aivnmst = models.IntegerField(db_column='AIVNMST', blank=True, null=True)
	aimgots = models.IntegerField(db_column='AIMGOTS', blank=True, null=True)
	asqhdr = models.BigIntegerField(db_column='ASQHDR', blank=True, null=True)
	asqtnum = models.SmallIntegerField(db_column='ASQTNUM', blank=True, null=True)
	asqfsn = models.IntegerField(db_column='ASQFSN', blank=True, null=True)
	aiahfsn = models.IntegerField(db_column='AIAHFSN', blank=True, null=True)
	aecdelay = models.IntegerField(db_column='AECDELAY', blank=True, null=True)
	aiaecti = models.IntegerField(db_column='AIAECTI', blank=True, null=True)
	aiasen = models.IntegerField(db_column='AIASEN', blank=True, null=True)
	aifdbid = models.IntegerField(db_column='AIFDBID', blank=True, null=True)
	aimgotss = models.IntegerField(db_column='AIMGOTSS', blank=True, null=True)
	aifcps = models.SmallIntegerField(db_column='AIFCPS', blank=True, null=True)
	aiftswth = models.IntegerField(db_column='AIFTSWTH', blank=True, null=True)
	aifrmlid = models.IntegerField(db_column='AIFRMLID', blank=True, null=True)
	aiftsid = models.IntegerField(db_column='AIFTSID', blank=True, null=True)
	aihismxb = models.IntegerField(db_column='AIHISMXB', blank=True, null=True)
	aihis192 = models.IntegerField(db_column='AIHIS192', blank=True, null=True)
	aihis348 = models.IntegerField(db_column='AIHIS348', blank=True, null=True)
	aihis604 = models.IntegerField(db_column='AIHIS604', blank=True, null=True)
	aihis860 = models.IntegerField(db_column='AIHIS860', blank=True, null=True)
	aifwen = models.IntegerField(db_column='AIFWEN', blank=True, null=True)
	aimgshce = models.IntegerField(db_column='AIMGSHCE', blank=True, null=True)
	aectype = models.SmallIntegerField(db_column='AECTYPE', blank=True, null=True)
	aecmode = models.TextField(db_column='AECMODE', blank=True)
	aistate = models.TextField(db_column='AISTATE', blank=True)
	aiaecenf = models.SmallIntegerField(db_column='AIAECENF', blank=True, null=True)
	aifiltyp = models.SmallIntegerField(db_column='AIFILTYP', blank=True, null=True)
	aimshobc = models.FloatField(db_column='AIMSHOBC', blank=True, null=True)
	aimshobe = models.FloatField(db_column='AIMSHOBE', blank=True, null=True)
	aimshotc = models.FloatField(db_column='AIMSHOTC', blank=True, null=True)
	aimshote = models.FloatField(db_column='AIMSHOTE', blank=True, null=True)
	aimshcbc = models.FloatField(db_column='AIMSHCBC', blank=True, null=True)
	aimshcbe = models.FloatField(db_column='AIMSHCBE', blank=True, null=True)
	aimshctc = models.FloatField(db_column='AIMSHCTC', blank=True, null=True)
	aimshcte = models.FloatField(db_column='AIMSHCTE', blank=True, null=True)
	aicfgdl1 = models.SmallIntegerField(db_column='AICFGDL1', blank=True, null=True)
	aicfgdl2 = models.SmallIntegerField(db_column='AICFGDL2', blank=True, null=True)
	aicfgdl3 = models.SmallIntegerField(db_column='AICFGDL3', blank=True, null=True)
	aicfgdl4 = models.SmallIntegerField(db_column='AICFGDL4', blank=True, null=True)
	aifoenfl = models.SmallIntegerField(db_column='AIFOENFL', blank=True, null=True)
	aimgfsn = models.IntegerField(db_column='AIMGFSN', blank=True, null=True)
	aimgtyp = models.IntegerField(db_column='AIMGTYP', blank=True, null=True)
	aiawvlen = models.IntegerField(db_column='AIAWVLEN', blank=True, null=True)
	aiagp1 = models.IntegerField(db_column='AIAGP1', blank=True, null=True)
	aiagp2 = models.IntegerField(db_column='AIAGP2', blank=True, null=True)
	aiagp3 = models.IntegerField(db_column='AIAGP3', blank=True, null=True)
	aiagp4 = models.IntegerField(db_column='AIAGP4', blank=True, null=True)
	aiagp5 = models.IntegerField(db_column='AIAGP5', blank=True, null=True)
	aiagp6 = models.IntegerField(db_column='AIAGP6', blank=True, null=True)
	aiagp7 = models.IntegerField(db_column='AIAGP7', blank=True, null=True)
	aiagp8 = models.IntegerField(db_column='AIAGP8', blank=True, null=True)
	aiagp9 = models.IntegerField(db_column='AIAGP9', blank=True, null=True)
	aiagp10 = models.IntegerField(db_column='AIAGP10', blank=True, null=True)
	agt1svy = models.SmallIntegerField(db_column='AGT1SVY', blank=True, null=True)
	agt1svz = models.SmallIntegerField(db_column='AGT1SVZ', blank=True, null=True)
	agt2svy = models.SmallIntegerField(db_column='AGT2SVY', blank=True, null=True)
	agt2svz = models.SmallIntegerField(db_column='AGT2SVZ', blank=True, null=True)
	agt3svy = models.SmallIntegerField(db_column='AGT3SVY', blank=True, null=True)
	agt3svz = models.SmallIntegerField(db_column='AGT3SVZ', blank=True, null=True)
	agt4svy = models.SmallIntegerField(db_column='AGT4SVY', blank=True, null=True)
	agt4svz = models.SmallIntegerField(db_column='AGT4SVZ', blank=True, null=True)
	aimgshen = models.SmallIntegerField(db_column='AIMGSHEN', blank=True, null=True)
	keywddoc = models.TextField(db_column='KEYWDDOC', blank=True)
	series = models.TextField(db_column='SERIES', blank=True)
	recnum = models.BigIntegerField(db_column='RECNUM', blank=False, null=False, primary_key = True)
	sunum = models.BigIntegerField(db_column='SUNUM', blank=True, null=True)
	slotnum = models.IntegerField(db_column='SLOTNUM', blank=True, null=True)
	segment = models.TextField(db_column='SEGMENT', blank=True)
	class Meta:
		managed = False
		db_table = 'aia_lev1_fits_header'
		get_latest_by = 'date_obs'
	
	def __unicode__(self):
		return unicode(self.recnum)


class AiaLev1FitsKeyword(models.Model):
	keyword = models.TextField(blank=False, primary_key = True)
	unit = models.TextField(blank=True)
	comment = models.TextField(blank=True)
	class Meta:
		managed = False
		db_table = 'aia_lev1_fits_keyword'
	
	def __unicode__(self):
		return unicode(self.keyword)

class HmiIc45sFitsHeader(models.Model):
	date = models.DateTimeField(db_column='DATE', blank=True, null=True)
	date_obs = models.DateTimeField(db_column='DATE-OBS', blank=True, null=True)
	telescop = models.TextField(db_column='TELESCOP', blank=True)
	instrume = models.TextField(db_column='INSTRUME', blank=True)
	wavelnth = models.FloatField(db_column='WAVELNTH', blank=True, null=True)
	camera = models.IntegerField(db_column='CAMERA', blank=True, null=True)
	bunit = models.TextField(db_column='BUNIT', blank=True)
	origin = models.TextField(db_column='ORIGIN', blank=True)
	content = models.TextField(db_column='CONTENT', blank=True)
	quality = models.IntegerField(db_column='QUALITY', blank=True, null=True)
	quallev1 = models.IntegerField(db_column='QUALLEV1', blank=True, null=True)
	history = models.TextField(db_column='HISTORY', blank=True)
	comment = models.TextField(db_column='COMMENT', blank=True)
	bld_vers = models.TextField(db_column='BLD_VERS', blank=True)
	hcamid = models.IntegerField(db_column='HCAMID', blank=True, null=True)
	source = models.TextField(db_column='SOURCE', blank=True)
	totvals = models.IntegerField(db_column='TOTVALS', blank=True, null=True)
	datavals = models.IntegerField(db_column='DATAVALS', blank=True, null=True)
	missvals = models.IntegerField(db_column='MISSVALS', blank=True, null=True)
	satvals = models.IntegerField(db_column='SATVALS', blank=True, null=True)
	datamin2 = models.FloatField(db_column='DATAMIN2', blank=True, null=True)
	datamax2 = models.FloatField(db_column='DATAMAX2', blank=True, null=True)
	datamed2 = models.FloatField(db_column='DATAMED2', blank=True, null=True)
	datamea2 = models.FloatField(db_column='DATAMEA2', blank=True, null=True)
	datarms2 = models.FloatField(db_column='DATARMS2', blank=True, null=True)
	dataske2 = models.FloatField(db_column='DATASKE2', blank=True, null=True)
	datakur2 = models.FloatField(db_column='DATAKUR2', blank=True, null=True)
	datamin = models.FloatField(db_column='DATAMIN', blank=True, null=True)
	datamax = models.FloatField(db_column='DATAMAX', blank=True, null=True)
	datamedn = models.FloatField(db_column='DATAMEDN', blank=True, null=True)
	datamean = models.FloatField(db_column='DATAMEAN', blank=True, null=True)
	datarms = models.FloatField(db_column='DATARMS', blank=True, null=True)
	dataskew = models.FloatField(db_column='DATASKEW', blank=True, null=True)
	datakurt = models.FloatField(db_column='DATAKURT', blank=True, null=True)
	ctype1 = models.TextField(db_column='CTYPE1', blank=True)
	ctype2 = models.TextField(db_column='CTYPE2', blank=True)
	crpix1 = models.FloatField(db_column='CRPIX1', blank=True, null=True)
	crpix2 = models.FloatField(db_column='CRPIX2', blank=True, null=True)
	crval1 = models.FloatField(db_column='CRVAL1', blank=True, null=True)
	crval2 = models.FloatField(db_column='CRVAL2', blank=True, null=True)
	cdelt1 = models.FloatField(db_column='CDELT1', blank=True, null=True)
	cdelt2 = models.FloatField(db_column='CDELT2', blank=True, null=True)
	cunit1 = models.TextField(db_column='CUNIT1', blank=True)
	cunit2 = models.TextField(db_column='CUNIT2', blank=True)
	crota2 = models.FloatField(db_column='CROTA2', blank=True, null=True)
	crder1 = models.FloatField(db_column='CRDER1', blank=True, null=True)
	crder2 = models.FloatField(db_column='CRDER2', blank=True, null=True)
	csyser1 = models.FloatField(db_column='CSYSER1', blank=True, null=True)
	csyser2 = models.FloatField(db_column='CSYSER2', blank=True, null=True)
	wcsname = models.TextField(db_column='WCSNAME', blank=True)
	dsun_obs = models.FloatField(db_column='DSUN_OBS', blank=True, null=True)
	dsun_ref = models.FloatField(db_column='DSUN_REF', blank=True, null=True)
	rsun_ref = models.FloatField(db_column='RSUN_REF', blank=True, null=True)
	crln_obs = models.FloatField(db_column='CRLN_OBS', blank=True, null=True)
	crlt_obs = models.FloatField(db_column='CRLT_OBS', blank=True, null=True)
	car_rot = models.IntegerField(db_column='CAR_ROT', blank=True, null=True)
	obs_vr = models.FloatField(db_column='OBS_VR', blank=True, null=True)
	obs_vw = models.FloatField(db_column='OBS_VW', blank=True, null=True)
	obs_vn = models.FloatField(db_column='OBS_VN', blank=True, null=True)
	rsun_obs = models.FloatField(db_column='RSUN_OBS', blank=True, null=True)
	t_obs = models.DateTimeField(db_column='T_OBS', blank=True, null=True)
	t_rec = models.DateTimeField(db_column='T_REC', blank=True, null=True)
	cadence = models.FloatField(db_column='CADENCE', blank=True, null=True)
	datasign = models.IntegerField(db_column='DATASIGN', blank=True, null=True)
	hflid = models.IntegerField(db_column='HFLID', blank=True, null=True)
	hcftid = models.IntegerField(db_column='HCFTID', blank=True, null=True)
	qlook = models.IntegerField(db_column='QLOOK', blank=True, null=True)
	cal_fsn = models.IntegerField(db_column='CAL_FSN', blank=True, null=True)
	lutquery = models.TextField(db_column='LUTQUERY', blank=True)
	tsel = models.FloatField(db_column='TSEL', blank=True, null=True)
	tfront = models.FloatField(db_column='TFRONT', blank=True, null=True)
	tintnum = models.IntegerField(db_column='TINTNUM', blank=True, null=True)
	sintnum = models.IntegerField(db_column='SINTNUM', blank=True, null=True)
	distcoef = models.TextField(db_column='DISTCOEF', blank=True)
	rotcoef = models.TextField(db_column='ROTCOEF', blank=True)
	odicoeff = models.IntegerField(db_column='ODICOEFF', blank=True, null=True)
	orocoeff = models.IntegerField(db_column='OROCOEFF', blank=True, null=True)
	polcalm = models.IntegerField(db_column='POLCALM', blank=True, null=True)
	codever0 = models.TextField(db_column='CODEVER0', blank=True)
	codever1 = models.TextField(db_column='CODEVER1', blank=True)
	codever2 = models.TextField(db_column='CODEVER2', blank=True)
	codever3 = models.TextField(db_column='CODEVER3', blank=True)
	calver64 = models.BigIntegerField(db_column='CALVER64', blank=True, null=True)
	series = models.TextField(db_column='SERIES', blank=True)
	recnum = models.BigIntegerField(db_column='RECNUM', blank=False, null=False, primary_key = True)
	sunum = models.BigIntegerField(db_column='SUNUM', blank=True, null=True)
	slotnum = models.IntegerField(db_column='SLOTNUM', blank=True, null=True)
	segment = models.TextField(db_column='SEGMENT', blank=True)
	class Meta:
		managed = False
		db_table = 'hmi_ic_45s_fits_header'
		get_latest_by = 'date_obs'
	
	def __unicode__(self):
		return unicode(self.recnum)

class HmiIc45sFitsKeyword(models.Model):
	keyword = models.TextField(blank=False, primary_key = True)
	unit = models.TextField(blank=True)
	comment = models.TextField(blank=True)
	class Meta:
		managed = False
		db_table = 'hmi_ic_45s_fits_keyword'
	
	def __unicode__(self):
		return unicode(self.keyword)

class HmiM45sFitsHeader(models.Model):
	date = models.DateTimeField(db_column='DATE', blank=True, null=True)
	date_obs = models.DateTimeField(db_column='DATE-OBS', blank=True, null=True)
	telescop = models.TextField(db_column='TELESCOP', blank=True)
	instrume = models.TextField(db_column='INSTRUME', blank=True)
	wavelnth = models.FloatField(db_column='WAVELNTH', blank=True, null=True)
	camera = models.IntegerField(db_column='CAMERA', blank=True, null=True)
	bunit = models.TextField(db_column='BUNIT', blank=True)
	origin = models.TextField(db_column='ORIGIN', blank=True)
	content = models.TextField(db_column='CONTENT', blank=True)
	quality = models.IntegerField(db_column='QUALITY', blank=True, null=True)
	quallev1 = models.IntegerField(db_column='QUALLEV1', blank=True, null=True)
	history = models.TextField(db_column='HISTORY', blank=True)
	comment = models.TextField(db_column='COMMENT', blank=True)
	bld_vers = models.TextField(db_column='BLD_VERS', blank=True)
	hcamid = models.IntegerField(db_column='HCAMID', blank=True, null=True)
	source = models.TextField(db_column='SOURCE', blank=True)
	totvals = models.IntegerField(db_column='TOTVALS', blank=True, null=True)
	datavals = models.IntegerField(db_column='DATAVALS', blank=True, null=True)
	missvals = models.IntegerField(db_column='MISSVALS', blank=True, null=True)
	satvals = models.IntegerField(db_column='SATVALS', blank=True, null=True)
	datamin2 = models.FloatField(db_column='DATAMIN2', blank=True, null=True)
	datamax2 = models.FloatField(db_column='DATAMAX2', blank=True, null=True)
	datamed2 = models.FloatField(db_column='DATAMED2', blank=True, null=True)
	datamea2 = models.FloatField(db_column='DATAMEA2', blank=True, null=True)
	datarms2 = models.FloatField(db_column='DATARMS2', blank=True, null=True)
	dataske2 = models.FloatField(db_column='DATASKE2', blank=True, null=True)
	datakur2 = models.FloatField(db_column='DATAKUR2', blank=True, null=True)
	datamin = models.FloatField(db_column='DATAMIN', blank=True, null=True)
	datamax = models.FloatField(db_column='DATAMAX', blank=True, null=True)
	datamedn = models.FloatField(db_column='DATAMEDN', blank=True, null=True)
	datamean = models.FloatField(db_column='DATAMEAN', blank=True, null=True)
	datarms = models.FloatField(db_column='DATARMS', blank=True, null=True)
	dataskew = models.FloatField(db_column='DATASKEW', blank=True, null=True)
	datakurt = models.FloatField(db_column='DATAKURT', blank=True, null=True)
	ctype1 = models.TextField(db_column='CTYPE1', blank=True)
	ctype2 = models.TextField(db_column='CTYPE2', blank=True)
	crpix1 = models.FloatField(db_column='CRPIX1', blank=True, null=True)
	crpix2 = models.FloatField(db_column='CRPIX2', blank=True, null=True)
	crval1 = models.FloatField(db_column='CRVAL1', blank=True, null=True)
	crval2 = models.FloatField(db_column='CRVAL2', blank=True, null=True)
	cdelt1 = models.FloatField(db_column='CDELT1', blank=True, null=True)
	cdelt2 = models.FloatField(db_column='CDELT2', blank=True, null=True)
	cunit1 = models.TextField(db_column='CUNIT1', blank=True)
	cunit2 = models.TextField(db_column='CUNIT2', blank=True)
	crota2 = models.FloatField(db_column='CROTA2', blank=True, null=True)
	crder1 = models.FloatField(db_column='CRDER1', blank=True, null=True)
	crder2 = models.FloatField(db_column='CRDER2', blank=True, null=True)
	csyser1 = models.FloatField(db_column='CSYSER1', blank=True, null=True)
	csyser2 = models.FloatField(db_column='CSYSER2', blank=True, null=True)
	wcsname = models.TextField(db_column='WCSNAME', blank=True)
	dsun_obs = models.FloatField(db_column='DSUN_OBS', blank=True, null=True)
	dsun_ref = models.FloatField(db_column='DSUN_REF', blank=True, null=True)
	rsun_ref = models.FloatField(db_column='RSUN_REF', blank=True, null=True)
	crln_obs = models.FloatField(db_column='CRLN_OBS', blank=True, null=True)
	crlt_obs = models.FloatField(db_column='CRLT_OBS', blank=True, null=True)
	car_rot = models.IntegerField(db_column='CAR_ROT', blank=True, null=True)
	obs_vr = models.FloatField(db_column='OBS_VR', blank=True, null=True)
	obs_vw = models.FloatField(db_column='OBS_VW', blank=True, null=True)
	obs_vn = models.FloatField(db_column='OBS_VN', blank=True, null=True)
	rsun_obs = models.FloatField(db_column='RSUN_OBS', blank=True, null=True)
	t_obs = models.DateTimeField(db_column='T_OBS', blank=True, null=True)
	t_rec = models.DateTimeField(db_column='T_REC', blank=True, null=True)
	cadence = models.FloatField(db_column='CADENCE', blank=True, null=True)
	datasign = models.IntegerField(db_column='DATASIGN', blank=True, null=True)
	hflid = models.IntegerField(db_column='HFLID', blank=True, null=True)
	hcftid = models.IntegerField(db_column='HCFTID', blank=True, null=True)
	qlook = models.IntegerField(db_column='QLOOK', blank=True, null=True)
	cal_fsn = models.IntegerField(db_column='CAL_FSN', blank=True, null=True)
	lutquery = models.TextField(db_column='LUTQUERY', blank=True)
	tsel = models.FloatField(db_column='TSEL', blank=True, null=True)
	tfront = models.FloatField(db_column='TFRONT', blank=True, null=True)
	tintnum = models.IntegerField(db_column='TINTNUM', blank=True, null=True)
	sintnum = models.IntegerField(db_column='SINTNUM', blank=True, null=True)
	distcoef = models.TextField(db_column='DISTCOEF', blank=True)
	rotcoef = models.TextField(db_column='ROTCOEF', blank=True)
	odicoeff = models.IntegerField(db_column='ODICOEFF', blank=True, null=True)
	orocoeff = models.IntegerField(db_column='OROCOEFF', blank=True, null=True)
	polcalm = models.IntegerField(db_column='POLCALM', blank=True, null=True)
	codever0 = models.TextField(db_column='CODEVER0', blank=True)
	codever1 = models.TextField(db_column='CODEVER1', blank=True)
	codever2 = models.TextField(db_column='CODEVER2', blank=True)
	codever3 = models.TextField(db_column='CODEVER3', blank=True)
	calver64 = models.BigIntegerField(db_column='CALVER64', blank=True, null=True)
	series = models.TextField(db_column='SERIES', blank=True)
	recnum = models.BigIntegerField(db_column='RECNUM', blank=False, null=False, primary_key = True)
	sunum = models.BigIntegerField(db_column='SUNUM', blank=True, null=True)
	slotnum = models.IntegerField(db_column='SLOTNUM', blank=True, null=True)
	segment = models.TextField(db_column='SEGMENT', blank=True)
	class Meta:
		managed = False
		db_table = 'hmi_m_45s_fits_header'
		get_latest_by = 'date_obs'
	
	def __unicode__(self):
		return unicode(self.recnum)

class HmiM45sFitsKeyword(models.Model):
	keyword = models.TextField(blank=False, primary_key = True)
	unit = models.TextField(blank=True)
	comment = models.TextField(blank=True)
	class Meta:
		managed = False
		db_table = 'hmi_m_45s_fits_keyword'
	
	def __unicode__(self):
		return unicode(self.keyword)
