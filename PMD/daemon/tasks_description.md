Requests
========

## get_data_request
  * check_data_local_availability
  * get_data_location_request
  * data_download_request
  * get_data_request

## data_download_request
 * pre_data_download
 * data_download
 * post_download_copy
 * update_fits_header_request

## get_data_location_request
 * check_data_local_availability
 * data_location_request
 * get_data_location_request

## data_location_request
 * locate_data
 * save_data_location

## delete_data_request
 * check_data_local_availability
 * delete_file
 * delete_database_record
 
## update_fits_header_request
 * check_data_local_availability
 * get_fits_header
 * update_fits_header

Tasks
=====

## check_data_local_availability
 * search local path in db
 * check file exists
 * return file path

## pre_data_download
 * asks folder to sum_svc
 * return folder path

## data_download
 * download data according to data site protocol
 * if no remote file
   * data_location_request
   * get_data_request

## post_data_download
 * tell sum_svc about new data

## locate_data
 * do jsoc_fetch http request

## save_data_location
 * update database

## delete_file
 * remove file from disk
 * if empty folder remove folder

## delete_database_record
 * remove local path from database

## get_fits_header
 * lookup fits header keyword values

## update_fits_header
 * update fits header
