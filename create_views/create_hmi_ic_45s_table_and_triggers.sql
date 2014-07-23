-- Create the table
CREATE TABLE pmd.hmi_ic_45s
(
   recnum bigint CONSTRAINT hmi_ic_45s_pkey PRIMARY KEY,
   sunum bigint,
   slotnum integer,
   segment text,
   date_obs timestamp without time zone,
   wavelnth real,
   quality integer,
   t_rec_index bigint,
   camera integer
);

-- Create the indexes
CREATE UNIQUE INDEX hmi_ic_45s_t_rec_index_camera_idx
  ON hmi_ic_45s
  USING btree
  (t_rec_index, camera)
TABLESPACE indexspace;

CREATE INDEX hmi_ic_45s_date_obs_idx
  ON hmi_ic_45s
  USING btree
  (date_obs)
TABLESPACE indexspace;

-- Create the trigger function
CREATE OR REPLACE FUNCTION hmi.populate_hmi_ic_45s() RETURNS TRIGGER AS $populate_hmi_ic_45s$
BEGIN
	BEGIN
		-- First we try an update. It will fail if the row didn't exist yet.
		UPDATE pmd.hmi_ic_45s
		SET
			recnum=NEW.recnum,
			sunum=NEW.sunum,
			slotnum=NEW.slotnum,
			segment=NEW.sg_000_file,
			date_obs=offset_to_utc(NEW.date__obs),
			wavelnth=6173.0,
			quality=NEW.quality
		WHERE
			t_rec_index=NEW.t_rec_index
			AND camera=NEW.camera
			AND recnum<NEW.recnum
		;
		-- Next we try a insert. It will not happen if the row exist already.
		INSERT INTO pmd.hmi_ic_45s (recnum, sunum, slotnum, segment, date_obs, wavelnth, quality, t_rec_index, camera)
		SELECT
			NEW.recnum,
			NEW.sunum,
			NEW.slotnum,
			NEW.sg_000_file,
			offset_to_utc(NEW.date__obs),
			6173.0,
			NEW.quality,
			NEW.t_rec_index,
			NEW.camera
		WHERE
			NOT EXISTS (
				SELECT 1
				FROM pmd.hmi_ic_45s
				WHERE
					t_rec_index=NEW.t_rec_index
					AND camera=NEW.camera
			)
		;
	-- If the insert fail we just keep on going
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Insertion failure for recnum %: %', NEW.recnum, SQLERRM ;
	END;
	RETURN NEW;
END;
$populate_hmi_ic_45s$ LANGUAGE plpgsql;


-- Create the trigger
CREATE TRIGGER trigger_populate_hmi_ic_45s
AFTER INSERT ON hmi.ic_45s
FOR EACH ROW
EXECUTE PROCEDURE hmi.populate_hmi_ic_45s();

-- Fill up the table
INSERT INTO pmd.hmi_ic_45s
(
   recnum,
   sunum,
   slotnum,
   segment,
   date_obs,
   wavelnth,
   quality,
   t_rec_index,
   camera
)
SELECT recnum, sunum, slotnum, sg_000_file, offset_to_utc(date__obs), 6173.0, quality, t_rec_index, camera
FROM (
   SELECT recnum, sunum, slotnum, sg_000_file, date__obs, quality, t_rec_index, camera, max(recnum) OVER (PARTITION BY t_rec_index, camera) AS latest_recnum
   FROM hmi.ic_45s
) AS foo
WHERE recnum = latest_recnum;
