#!/usr/bin/python
import pyfits
import pandas
exported_fits = "aia.88833409.exp.fits"
keywords_file = "aia.keywords.csv"
db_file = "aia.88833409.csv"
series_name = "aia.lev1"
view_name = "aia_lev1_fits_header"


hdus =  pyfits.open(exported_fits)
hdus.verify('fix')
header = hdus[1].header

db_val = pandas.read_csv(db_file, quotechar = '"')
db_val.rename(columns=lambda x: x.upper(), inplace=True)
keywords = pandas.read_csv(keywords_file, index_col="keywordname", quotechar = '"')

print "CREATE VIEW", view_name, "AS SELECT"

for key in header:
	if key in ["COMMENT", "HISTORY"]:
		print 'tbl.{tbl_key} AS "{key}",'.format(tbl_key = key, key = key)
	elif key in db_val:
		if header[key] == type(header[key])(db_val.loc[0, key]):
			print 'tbl.{tbl_key} AS "{key}",'.format(tbl_key = key, key = key)
		elif type(header[key]) == float and float(db_val.loc[0, key]) != 0 and (0.999 < header[key]/float(db_val.loc[0, key]) < 1.001):
			print 'tbl.{tbl_key} AS "{key}",'.format(tbl_key = key, key = key)
		else:
			if key in keywords.index and keywords.loc[key, "type"] == "time":
				if keywords.loc[key, "unit"] == "ISO":
					print 'offset_to_utc(tbl.{tbl_key}) AS "{key}",'.format(tbl_key = key, key = key)
				elif keywords.loc[key, "unit"] == "TAI":
					print 'offset_to_tai(tbl.{tbl_key}) AS "{key}",'.format(tbl_key = key, key = key)
				else:
					print 'tbl.{tbl_key} AS "{key}",'.format(tbl_key = key, key = key), "UNKNOWN CONVERSION", db_val.loc[0, key], "=>", header[key]
			else:
				print 'tbl.{tbl_key} AS "{key}",'.format(tbl_key = key, key = key), "UNKNOWN CONVERSION", db_val.loc[0, key], "=>", header[key]
	elif key in keywords.index and keywords.loc[key, "isconstant"] != 0:
		if keywords.loc[key, "type"] == "string":
			print 'CAST(\'{constant}\' AS TEXT) AS "{key}",'.format(constant = header[key], key = key)
		elif keywords.loc[key, "type"] == "double":
			print 'CAST({constant} AS DOUBLE PRECISION) AS "{key}",'.format(constant = header[key], key = key)
		elif keywords.loc[key, "type"] == "int":
			print 'CAST({constant} AS INTEGER) AS "{key}",'.format(constant = header[key], key = key)
		else:
			print 'CAST({constant} AS REAL) AS "{key}",'.format(constant = header[key], key = key)
	else:
		print key, "NOT FOUND"

print "CAST('"+series_name+"' AS TEXT) AS \"SERIES\"",
print 'tbl.SUNUM AS "SUNUM",'
print 'tbl.SLOTNUM AS "SLOTNUM",'
print 'tbl.sg_000_file AS "SEGMENT"'
print "FROM", series_name,"AS tbl;"
