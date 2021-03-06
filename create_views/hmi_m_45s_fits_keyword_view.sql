CREATE VIEW hmi_m_45s_fits_keyword AS (
	SELECT
		CASE WHEN description ~ E'\\[.+\\].*' THEN
			(regexp_matches(description, E'\\[(.+)\\].*'))[1]
		ELSE
			upper(keywordname)
		END AS keyword,
		CASE WHEN lower(unit) = 'none' THEN
			NULL
		ELSE
			unit
		END AS unit,
		CASE WHEN description ~ E'\\[.+\\].*' THEN
			(regexp_matches(description, E'\\[.+\\]\s*(.*)'))[1]
		ELSE
			description
		END AS comment
	FROM hmi.drms_keyword WHERE seriesname = 'hmi.m_45s' AND keywordname NOT IN ('HISTORY', 'COMMENT')
) UNION (
	SELECT * FROM (
	VALUES
	('SERIES', null, 'JSOC Series Name'),
	('RECNUM', null, 'JSOC Record Number'),
	('SUNUM', null, 'JSOC Storage Unit Number'),
	('SLOTNUM', null, 'JSOC Slot Number'),
	('SEGMENT', null, 'JSOC Segment File Name')
	) AS q (keyword, unit, comment)
);

