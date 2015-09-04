-- Create the trigger when update/insert happen on records

-- Must be set for each record table
-- Set as an after update trigger
-- Take 1 argument, the data_series_name
CREATE OR REPLACE FUNCTION pmd.update_local_data() RETURNS TRIGGER AS $update_local_data$
BEGIN
	BEGIN
		-- If the sunum is updated then we need to delete the old file
		IF NEW.sunum <> OLD.sunum THEN
			INSERT INTO pmd.data_delete_request (data_series_name, sunum, slotnum, segment, recnum, status, priority, requested, updated)
			VALUES (TG_ARGV[0], OLD.sunum, OLD.slotnum, OLD.segment, OLD.recnum, 'NEW', 0, now(), now());
		-- If the recnum is larger we update the meta-data
		ELSIF NEW.recnum > OLD.recnum THEN
			INSERT INTO pmd.metadata_update_request (data_series_name, sunum, slotnum, segment, recnum, status, priority, requested, updated, new_recnum)
			VALUES (TG_ARGV[0], OLD.sunum, OLD.slotnum, OLD.segment, OLD.recnum, 'NEW', 0, now(), now(), NEW.recnum);
		END IF;
	-- If the insert fail we just keep on going
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Insertion failure for data_series % recnum %: %', TG_ARGV[0], NEW.recnum, SQLERRM ;
	END;
	RETURN NEW;
END;
$update_local_data$ LANGUAGE plpgsql;

-- Create the triggers
DROP TRIGGER IF EXISTS trigger_update_local_data ON pmd.aia_lev1;
CREATE TRIGGER trigger_update_local_data
AFTER UPDATE ON pmd.aia_lev1
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_local_data('aia_lev1');

DROP TRIGGER IF EXISTS trigger_update_local_data ON pmd.hmi_ic_45s;
CREATE TRIGGER trigger_update_local_data
AFTER UPDATE ON pmd.hmi_ic_45s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_local_data('hmi_ic_45s');

DROP TRIGGER IF EXISTS trigger_update_local_data ON pmd.hmi_m_45s;
CREATE TRIGGER trigger_update_local_data
AFTER UPDATE ON pmd.hmi_m_45s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_local_data('hmi_m_45s');

DROP TRIGGER IF EXISTS trigger_update_local_data ON pmd.hmi_mharp_720s;
CREATE TRIGGER trigger_update_local_data
AFTER UPDATE ON pmd.hmi_mharp_720s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_local_data('hmi_mharp_720s');

-- Must be set for each record table
-- Set as an after insert or update trigger
-- Take 1 argument, the data_series_name

CREATE OR REPLACE FUNCTION pmd.update_remote_location() RETURNS TRIGGER AS $update_remote_location$
DECLARE
	proactive_data_sites CURSOR FOR SELECT name FROM pmd.data_site WHERE data_location_proactive = 'true';
BEGIN
	BEGIN
		-- If it is an insertion ot if the sunum is updated then we need to do a data location request
		IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.sunum <> OLD.sunum)  THEN
			FOR proactive_data_site IN proactive_data_sites LOOP
				INSERT INTO pmd.data_location_request (data_series_name, sunum, slotnum, segment, recnum, status, priority, requested, updated, data_site_name)
				VALUES (TG_ARGV[0], NEW.sunum, NEW.slotnum, NEW.segment, NEW.recnum, 'NEW', 0, now(), now(), proactive_data_site.name);
			END LOOP;
		END IF;
	-- If the insert fail we just keep on going
	EXCEPTION
		WHEN OTHERS THEN
			RAISE WARNING 'Insertion failure for data_series % recnum %: %', TG_ARGV[0], NEW.recnum, SQLERRM ;
	END;
	RETURN NEW;
END;
$update_remote_location$ LANGUAGE plpgsql;


-- Create the triggers
DROP TRIGGER IF EXISTS trigger_update_remote_location ON pmd.aia_lev1;
CREATE TRIGGER trigger_update_remote_location
AFTER INSERT OR UPDATE ON pmd.aia_lev1
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_remote_location('aia_lev1');

DROP TRIGGER IF EXISTS trigger_update_remote_location ON pmd.hmi_ic_45s;
CREATE TRIGGER trigger_update_remote_location
AFTER INSERT OR UPDATE ON pmd.hmi_ic_45s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_remote_location('hmi_ic_45s');

DROP TRIGGER IF EXISTS trigger_update_remote_location ON pmd.hmi_m_45s;
CREATE TRIGGER trigger_update_remote_location
AFTER INSERT OR UPDATE ON pmd.hmi_m_45s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_remote_location('hmi_m_45s');

DROP TRIGGER IF EXISTS trigger_update_remote_location ON pmd.hmi_mharp_720s;
CREATE TRIGGER trigger_update_remote_location
AFTER INSERT OR UPDATE ON pmd.hmi_mharp_720s
FOR EACH ROW
EXECUTE PROCEDURE pmd.update_remote_location('hmi_mharp_720s');
