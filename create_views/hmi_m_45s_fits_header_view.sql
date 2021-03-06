CREATE VIEW hmi_m_45s_fits_header AS SELECT
offset_to_utc(tbl.DATE) AS "DATE",
offset_to_utc(tbl.DATE__OBS) AS "DATE-OBS",
CAST('SDO/HMI' AS TEXT) AS "TELESCOP",
tbl.INSTRUME AS "INSTRUME",
CAST(6173.0 AS REAL) AS "WAVELNTH",
tbl.CAMERA AS "CAMERA",
CAST('Gauss' AS TEXT) AS "BUNIT",
CAST('SDO/JSOC-SDP' AS TEXT) AS "ORIGIN",
CAST('MAGNETOGRAM' AS TEXT) AS "CONTENT",
tbl.QUALITY AS "QUALITY",
tbl.QUALLEV1 AS "QUALLEV1",
tbl.HISTORY AS "HISTORY",
tbl.COMMENT AS "COMMENT",
tbl.BLD_VERS AS "BLD_VERS",
tbl.HCAMID AS "HCAMID",
tbl.SOURCE AS "SOURCE",
tbl.TOTVALS AS "TOTVALS",
tbl.DATAVALS AS "DATAVALS",
tbl.MISSVALS AS "MISSVALS",
tbl.SATVALS AS "SATVALS",
tbl.DATAMIN2 AS "DATAMIN2",
tbl.DATAMAX2 AS "DATAMAX2",
tbl.DATAMED2 AS "DATAMED2",
tbl.DATAMEA2 AS "DATAMEA2",
tbl.DATARMS2 AS "DATARMS2",
tbl.DATASKE2 AS "DATASKE2",
tbl.DATAKUR2 AS "DATAKUR2",
tbl.DATAMIN AS "DATAMIN",
tbl.DATAMAX AS "DATAMAX",
tbl.DATAMEDN AS "DATAMEDN",
tbl.DATAMEAN AS "DATAMEAN",
tbl.DATARMS AS "DATARMS",
tbl.DATASKEW AS "DATASKEW",
tbl.DATAKURT AS "DATAKURT",
CAST('HPLN-TAN' AS TEXT) AS "CTYPE1",
CAST('HPLT-TAN' AS TEXT) AS "CTYPE2",
tbl.CRPIX1 AS "CRPIX1",
tbl.CRPIX2 AS "CRPIX2",
CAST(0.0 AS REAL) AS "CRVAL1",
CAST(0.0 AS REAL) AS "CRVAL2",
tbl.CDELT1 AS "CDELT1",
tbl.CDELT2 AS "CDELT2",
CAST('arcsec' AS TEXT) AS "CUNIT1",
CAST('arcsec' AS TEXT) AS "CUNIT2",
tbl.CROTA2 AS "CROTA2",
tbl.CRDER1 AS "CRDER1",
tbl.CRDER2 AS "CRDER2",
tbl.CSYSER1 AS "CSYSER1",
tbl.CSYSER2 AS "CSYSER2",
CAST('Helioprojective-cartesian' AS TEXT) AS "WCSNAME",
tbl.DSUN_OBS AS "DSUN_OBS",
CAST(149597870691.0 AS DOUBLE PRECISION) AS "DSUN_REF",
CAST(696000000.0 AS DOUBLE PRECISION) AS "RSUN_REF",
tbl.CRLN_OBS AS "CRLN_OBS",
tbl.CRLT_OBS AS "CRLT_OBS",
tbl.CAR_ROT AS "CAR_ROT",
tbl.OBS_VR AS "OBS_VR",
tbl.OBS_VW AS "OBS_VW",
tbl.OBS_VN AS "OBS_VN",
tbl.RSUN_OBS AS "RSUN_OBS",
offset_to_tai(tbl.T_OBS) AS "T_OBS",
offset_to_tai(tbl.T_REC) AS "T_REC",
CAST(45.0 AS REAL) AS "CADENCE",
CAST(1 AS INTEGER) AS "DATASIGN",
tbl.HFLID AS "HFLID",
tbl.HCFTID AS "HCFTID",
CAST(0 AS INTEGER) AS "QLOOK",
tbl.CAL_FSN AS "CAL_FSN",
tbl.LUTQUERY AS "LUTQUERY",
tbl.TSEL AS "TSEL",
tbl.TFRONT AS "TFRONT",
tbl.TINTNUM AS "TINTNUM",
tbl.SINTNUM AS "SINTNUM",
tbl.DISTCOEF AS "DISTCOEF",
tbl.ROTCOEF AS "ROTCOEF",
tbl.ODICOEFF AS "ODICOEFF",
tbl.OROCOEFF AS "OROCOEFF",
tbl.POLCALM AS "POLCALM",
tbl.CODEVER0 AS "CODEVER0",
tbl.CODEVER1 AS "CODEVER1",
tbl.CODEVER2 AS "CODEVER2",
tbl.CODEVER3 AS "CODEVER3",
tbl.CALVER64 AS "CALVER64",
CAST('hmi.m_45s' AS TEXT) AS "SERIES",
tbl.RECNUM AS "RECNUM",
tbl.SUNUM AS "SUNUM",
tbl.SLOTNUM AS "SLOTNUM",
tbl.sg_000_file AS "SEGMENT"
FROM hmi.m_45s AS tbl;
