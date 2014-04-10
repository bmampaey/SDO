CREATE VIEW aia_lev1_fits_header AS SELECT
tbl.BLD_VERS AS "BLD_VERS",
CAST(1.0 AS REAL) AS "LVL_NUM",
offset_to_utc(tbl.T_REC) AS "T_REC",
CAST('SDO/JSOC-SDP' AS TEXT) AS "ORIGIN",
offset_to_utc(tbl.DATE) AS "DATE",
CAST('SDO/AIA' AS TEXT) AS "TELESCOP",
tbl.INSTRUME AS "INSTRUME",
offset_to_utc(tbl.DATE__OBS) AS "DATE-OBS",
offset_to_utc(tbl.T_OBS) AS "T_OBS",
tbl.CAMERA AS "CAMERA",
tbl.IMG_TYPE AS "IMG_TYPE",
tbl.EXPTIME AS "EXPTIME",
tbl.EXPSDEV AS "EXPSDEV",
tbl.INT_TIME AS "INT_TIME",
tbl.WAVELNTH AS "WAVELNTH",
CAST('angstrom' AS TEXT) AS "WAVEUNIT",
tbl.WAVE_STR AS "WAVE_STR",
tbl.FSN AS "FSN",
tbl.FID AS "FID",
tbl.QUALLEV0 AS "QUALLEV0",
tbl.QUALITY AS "QUALITY",
tbl.TOTVALS AS "TOTVALS",
tbl.DATAVALS AS "DATAVALS",
tbl.MISSVALS AS "MISSVALS",
tbl.PERCENTD AS "PERCENTD",
tbl.DATAMIN AS "DATAMIN",
tbl.DATAMAX AS "DATAMAX",
tbl.DATAMEDN AS "DATAMEDN",
tbl.DATAMEAN AS "DATAMEAN",
tbl.DATARMS AS "DATARMS",
tbl.DATASKEW AS "DATASKEW",
tbl.DATAKURT AS "DATAKURT",
tbl.DATACENT AS "DATACENT",
tbl.DATAP01 AS "DATAP01",
tbl.DATAP10 AS "DATAP10",
tbl.DATAP25 AS "DATAP25",
tbl.DATAP75 AS "DATAP75",
tbl.DATAP90 AS "DATAP90",
tbl.DATAP95 AS "DATAP95",
tbl.DATAP98 AS "DATAP98",
tbl.DATAP99 AS "DATAP99",
tbl.NSATPIX AS "NSATPIX",
tbl.OSCNMEAN AS "OSCNMEAN",
tbl.OSCNRMS AS "OSCNRMS",
tbl.FLAT_REC AS "FLAT_REC",
tbl.NSPIKES AS "NSPIKES",
tbl.CTYPE1 AS "CTYPE1",
tbl.CUNIT1 AS "CUNIT1",
tbl.CRVAL1 AS "CRVAL1",
tbl.CDELT1 AS "CDELT1",
tbl.CRPIX1 AS "CRPIX1",
tbl.CTYPE2 AS "CTYPE2",
tbl.CUNIT2 AS "CUNIT2",
tbl.CRVAL2 AS "CRVAL2",
tbl.CDELT2 AS "CDELT2",
tbl.CRPIX2 AS "CRPIX2",
tbl.CROTA2 AS "CROTA2",
tbl.R_SUN AS "R_SUN",
tbl.MPO_REC AS "MPO_REC",
tbl.INST_ROT AS "INST_ROT",
tbl.IMSCL_MP AS "IMSCL_MP",
tbl.X0_MP AS "X0_MP",
tbl.Y0_MP AS "Y0_MP",
tbl.ASD_REC AS "ASD_REC",
tbl.SAT_Y0 AS "SAT_Y0",
tbl.SAT_Z0 AS "SAT_Z0",
tbl.SAT_ROT AS "SAT_ROT",
tbl.ACS_MODE AS "ACS_MODE",
tbl.ACS_ECLP AS "ACS_ECLP",
tbl.ACS_SUNP AS "ACS_SUNP",
tbl.ACS_SAFE AS "ACS_SAFE",
tbl.ACS_CGT AS "ACS_CGT",
tbl.ORB_REC AS "ORB_REC",
CAST(149597870691.0 AS DOUBLE PRECISION) AS "DSUN_REF",
tbl.DSUN_OBS AS "DSUN_OBS",
CAST(696000000.0 AS DOUBLE PRECISION) AS "RSUN_REF",
tbl.RSUN_OBS AS "RSUN_OBS",
tbl.GAEX_OBS AS "GAEX_OBS",
tbl.GAEY_OBS AS "GAEY_OBS",
tbl.GAEZ_OBS AS "GAEZ_OBS",
tbl.HAEX_OBS AS "HAEX_OBS",
tbl.HAEY_OBS AS "HAEY_OBS",
tbl.HAEZ_OBS AS "HAEZ_OBS",
tbl.OBS_VR AS "OBS_VR",
tbl.OBS_VW AS "OBS_VW",
tbl.OBS_VN AS "OBS_VN",
tbl.CRLN_OBS AS "CRLN_OBS",
tbl.CRLT_OBS AS "CRLT_OBS",
tbl.CAR_ROT AS "CAR_ROT",
tbl.HGLN_OBS AS "HGLN_OBS",
tbl.HGLT_OBS AS "HGLT_OBS",
tbl.ROI_NWIN AS "ROI_NWIN",
tbl.ROI_SUM AS "ROI_SUM",
tbl.ROI_NAX1 AS "ROI_NAX1",
tbl.ROI_NAY1 AS "ROI_NAY1",
tbl.ROI_LLX1 AS "ROI_LLX1",
tbl.ROI_LLY1 AS "ROI_LLY1",
tbl.ROI_NAX2 AS "ROI_NAX2",
tbl.ROI_NAY2 AS "ROI_NAY2",
tbl.ROI_LLX2 AS "ROI_LLX2",
tbl.ROI_LLY2 AS "ROI_LLY2",
CAST('DN' AS TEXT) AS "PIXLUNIT",
tbl.DN_GAIN AS "DN_GAIN",
tbl.EFF_AREA AS "EFF_AREA",
tbl.EFF_AR_V AS "EFF_AR_V",
tbl.TEMPCCD AS "TEMPCCD",
tbl.TEMPGT AS "TEMPGT",
tbl.TEMPSMIR AS "TEMPSMIR",
tbl.TEMPFPAD AS "TEMPFPAD",
tbl.ISPSNAME AS "ISPSNAME",
offset_to_utc(tbl.ISPPKTIM) AS "ISPPKTIM",
tbl.ISPPKTVN AS "ISPPKTVN",
tbl.AIVNMST AS "AIVNMST",
tbl.AIMGOTS AS "AIMGOTS",
tbl.ASQHDR AS "ASQHDR",
tbl.ASQTNUM AS "ASQTNUM",
tbl.ASQFSN AS "ASQFSN",
tbl.AIAHFSN AS "AIAHFSN",
tbl.AECDELAY AS "AECDELAY",
tbl.AIAECTI AS "AIAECTI",
tbl.AIASEN AS "AIASEN",
tbl.AIFDBID AS "AIFDBID",
tbl.AIMGOTSS AS "AIMGOTSS",
tbl.AIFCPS AS "AIFCPS",
tbl.AIFTSWTH AS "AIFTSWTH",
tbl.AIFRMLID AS "AIFRMLID",
tbl.AIFTSID AS "AIFTSID",
tbl.AIHISMXB AS "AIHISMXB",
tbl.AIHIS192 AS "AIHIS192",
tbl.AIHIS348 AS "AIHIS348",
tbl.AIHIS604 AS "AIHIS604",
tbl.AIHIS860 AS "AIHIS860",
tbl.AIFWEN AS "AIFWEN",
tbl.AIMGSHCE AS "AIMGSHCE",
tbl.AECTYPE AS "AECTYPE",
tbl.AECMODE AS "AECMODE",
tbl.AISTATE AS "AISTATE",
tbl.AIAECENF AS "AIAECENF",
tbl.AIFILTYP AS "AIFILTYP",
tbl.AIMSHOBC AS "AIMSHOBC",
tbl.AIMSHOBE AS "AIMSHOBE",
tbl.AIMSHOTC AS "AIMSHOTC",
tbl.AIMSHOTE AS "AIMSHOTE",
tbl.AIMSHCBC AS "AIMSHCBC",
tbl.AIMSHCBE AS "AIMSHCBE",
tbl.AIMSHCTC AS "AIMSHCTC",
tbl.AIMSHCTE AS "AIMSHCTE",
tbl.AICFGDL1 AS "AICFGDL1",
tbl.AICFGDL2 AS "AICFGDL2",
tbl.AICFGDL3 AS "AICFGDL3",
tbl.AICFGDL4 AS "AICFGDL4",
tbl.AIFOENFL AS "AIFOENFL",
tbl.AIMGFSN AS "AIMGFSN",
tbl.AIMGTYP AS "AIMGTYP",
tbl.AIAWVLEN AS "AIAWVLEN",
tbl.AIAGP1 AS "AIAGP1",
tbl.AIAGP2 AS "AIAGP2",
tbl.AIAGP3 AS "AIAGP3",
tbl.AIAGP4 AS "AIAGP4",
tbl.AIAGP5 AS "AIAGP5",
tbl.AIAGP6 AS "AIAGP6",
tbl.AIAGP7 AS "AIAGP7",
tbl.AIAGP8 AS "AIAGP8",
tbl.AIAGP9 AS "AIAGP9",
tbl.AIAGP10 AS "AIAGP10",
tbl.AGT1SVY AS "AGT1SVY",
tbl.AGT1SVZ AS "AGT1SVZ",
tbl.AGT2SVY AS "AGT2SVY",
tbl.AGT2SVZ AS "AGT2SVZ",
tbl.AGT3SVY AS "AGT3SVY",
tbl.AGT3SVZ AS "AGT3SVZ",
tbl.AGT4SVY AS "AGT4SVY",
tbl.AGT4SVZ AS "AGT4SVZ",
tbl.AIMGSHEN AS "AIMGSHEN",
CAST('http://www.lmsal.com/sdodocs/aiafitskeywords.pdf' AS TEXT) AS "KEYWDDOC",
CAST('aia.lev1' AS TEXT) AS "SERIES",
tbl.RECNUM AS "RECNUM",
tbl.SUNUM AS "SUNUM",
tbl.SLOTNUM AS "SLOTNUM",
tbl.sg_000_file AS "SEGMENT"
FROM aia.lev1 AS tbl;
