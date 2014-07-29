-- Create the table
CREATE TABLE pmd.aia_lev1
(
   recnum bigint CONSTRAINT aia_lev1_pkey PRIMARY KEY,
   sunum bigint,
   slotnum integer,
   segment text,
   date_obs timestamp without time zone,
   wavelnth real,
   quality integer,
   t_rec_index bigint,
   fsn integer
);

-- Create the indexes
CREATE UNIQUE INDEX aia_lev1_t_rec_index_fsn_idx
  ON aia_lev1
  USING btree
  (t_rec_index, fsn)
TABLESPACE indexspace;

CREATE INDEX aia_lev1_date_obs_idx
  ON aia_lev1
  USING btree
  (date_obs)
TABLESPACE indexspace;

-- Create the trigger function
CREATE OR REPLACE FUNCTION aia.populate_aia_lev1() RETURNS TRIGGER AS $populate_aia_lev1$
BEGIN
	BEGIN
		-- First we try an update. It will fail if the row didn't exist yet.
		UPDATE pmd.aia_lev1
		SET
			recnum=NEW.recnum,
			sunum=NEW.sunum,
			slotnum=NEW.slotnum,
			segment=NEW.sg_000_file,
			date_obs=offset_to_utc(NEW.date__obs),
			wavelnth=NEW.wavelnth,
			quality=NEW.quality
		WHERE
			t_rec_index=NEW.t_rec_index
			AND fsn=NEW.fsn
			AND recnum<NEW.recnum
		;
		-- Next we try a insert. It will not happen if the row exist already.
		INSERT INTO pmd.aia_lev1 (recnum, sunum, slotnum, segment, date_obs, wavelnth, quality, t_rec_index, fsn)
		SELECT
			NEW.recnum,
			NEW.sunum,
			NEW.slotnum,
			NEW.sg_000_file,
			offset_to_utc(NEW.date__obs),
			NEW.wavelnth,
			NEW.quality,
			NEW.t_rec_index,
			NEW.fsn
		WHERE
			NOT EXISTS (
				SELECT 1
				FROM pmd.aia_lev1
				WHERE
					t_rec_index=NEW.t_rec_index
					AND fsn=NEW.fsn
				)
		;
	-- If the insert fail we just keep on going
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Insertion failure for recnum %: %', NEW.recnum, SQLERRM ;
	END;
	RETURN NEW;
END;
$populate_aia_lev1$ LANGUAGE plpgsql;


-- Create the trigger
CREATE TRIGGER trigger_populate_aia_lev1
AFTER INSERT ON aia.lev1
FOR EACH ROW
EXECUTE PROCEDURE aia.populate_aia_lev1();

-- Fill up the table
INSERT INTO pmd.aia_lev1
(
   recnum,
   sunum,
   slotnum,
   segment,
   date_obs,
   wavelnth,
   quality,
   t_rec_index,
   fsn
)
SELECT recnum, sunum, slotnum, sg_000_file, offset_to_utc(date__obs), wavelnth, quality, t_rec_index, fsn
FROM (
   SELECT recnum, sunum, slotnum, sg_000_file, date__obs, wavelnth, quality, t_rec_index, fsn, max(recnum) OVER (PARTITION BY t_rec_index, fsn) AS latest_recnum
   FROM aia.lev1
) AS foo
WHERE recnum = latest_recnum;


