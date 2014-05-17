/*
TODO
Improve the download
*/

// Global variables
selected_tab_id = "#tab_aia.lev1";
search_request = {};
download_popup = null;
debug = true;

// Constants
download_fits_file_link = '/sdodb/netdrms/get_fits_file';
export_csv_link = '/sdodb/netdrms/export_csv';
max_zip = 50;
max_export = 50;
max_online = 50;
max_retention = 50;

function log(a, b, c, d, e)
{
	if(debug)
	{
		var bits = [a, b, c, d, e];
		var message = "";
		for (var i = 0; i<bits.length; ++i)
		{
			if(bits[i] !== undefined)
			message += bits[i].toString() + " ";
		}
		$("#debug_console").append('<p style="margin-top:1em;">'+message+'</p>');
	}
}


function alert_user(message, box)
{
	if(box == null)
	{
		box = $('<div class="ui-state-error"><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Note:</span>' + message + '</div>');
		box.dialog({
			modal: true,
			draggable: false,
			title: "Error",
			resizable: false,
			close: function(event, ui) {$( this ).remove();},
			buttons: {
				Ok: function() {
					$( this ).dialog( "close" );
				}
			}
		});
	}
	else
	{
		box.removeClass("ui-state-highlight").addClass("ui-state-error");
		box.html('<p><span class="ui-icon ui-icon-alert" style="float: left; margin-right: 0.3em;">Note:</span><strong>' + message + '</strong></p>');
	}
}

function inform_user(message, box)
{
	if(box == null)
	{
		box = $('<div class="ui-state-highlight"><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Note:</span>' + message + '</div>');
		box.dialog({
			modal: false,
			draggable: false,
			title: "Note",
			resizable: false,
			close: function(event, ui) {$( this ).remove();},
			buttons: {
				Ok: function() {
					$( this ).dialog( "close" );
				}
			}
		});
		//box.remove();
	}
	else
	{
		box.removeClass("ui-state-error").addClass("ui-state-highlight");
		box.html('<p><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Note:</span>' + message + '</p>').effect("highlight", {}, 2000);
	}
}

function get_start_date()
{
	return Date.parse($("#id_start_date").val());
}

function get_end_date()
{
	return Date.parse($("#id_end_date").val());
}


function select_all(action)
{
	var check_boxes = $("table.search_results_table input", selected_tab_id);
	switch(action.toLowerCase())
	{
		case 'select':
			check_boxes.each(function(){$(this).attr('checked', true)});
			break;
		case 'unselect':
			check_boxes.each(function(){$(this).attr('checked', false)});
			break;
		case 'inverse':
			check_boxes.each(function(){$(this).attr('checked', ! $(this).attr('checked'))});
			break;
	}
}


function make_result_row(series_name, row)
{
	var recnum = String(row[0]);
	var new_row = $('<tr id="'+recnum+'" class="' +availability+ '"/>');
	var title = series_name + " " + row[3];
	if (series_name == "aia.lev1")
		title += " " + row[4] + "&Aring;";
	// First elems of the table are preview and download buttons
	var button = preview_button(series_name, recnum, title);
	new_row.append($('<td class="preview"></td>').append(button));
	// Next elem of the table is the checkbox with the recnum as value
	new_row.append('<td><input type="checkbox" name="recnum[]" value="' + recnum + '" /></td>');
	// The rest is just keyword values
	for (var i = 3; i < row.length; i++)
	{
			new_row.append('<td>' + row[i] + '</td>');
	}
	return new_row;
}

function append_table_rows(table, search_results, first_search) 
{
	var table_body = $('tbody', table);
	// If we don't know if it is a first search, we look if the table is empty

	if(first_search == null)
		first_search = $('tr', table_body).length > 0;

	for (var i = 0; i < search_results.data.length; i++)
	{	
		var new_row = make_result_row(search_results.series_name, search_results.data[i]);
		
		// If a row exists with that recnum, we just replace the old row with the new one
		if(!first_search)
		{
			// First elem in the row is the recnum
			var old_row = $('#'+search_results.data[i][0], table_body);
			if(old_row.length > 0)
			{
				old_row.replaceWith(new_row);
				continue;
			}
		}
		table_body.append(new_row);
	}
	
	// Create the table headers
	make_table_headers(table, search_results.headers);
			
	// Update the sortable plugin
	table.trigger("update");
	
	// Set correctly the size of the columns
	var header_width = 0;
	var columns_width = Array();
	$("tr:first td", table_body).each(function() {
		header_width+=$(this).outerWidth();
		columns_width.push($(this).width());
	});
	
	log("header_width:", header_width);
	log("columns_width:", columns_width);
	
	var table_head = $("thead", table);
	table_head.width(header_width);
	$("tr th",  table_head ).map(function(i, header){
		$(header).width(columns_width[i]);
	});
	
}

function get_table_headers(table)
{
	var headers = Array();
	$('thead th', table).each(function() {headers.push($(this).text());} );
	return headers.slice(5);
}

function make_table_headers(table, keywords)
{
	var excluded_headers = ['recnum', 'retain', 'online'];
	var table_headers = get_table_headers(table);
	var headers_row = $('thead > tr', table);
	// If I have already some headers, I must not duplicate them
	if(table_headers.length > 0)
	{
		for(var i = 0; i < keywords.length; i++)
		{
			// We test the keyword is not excluded, and not already amongst the headers
			if(excluded_headers.indexOf(keywords[i]) < 0 && table_headers.indexOf(keywords[i]) < 0)
			{
				headers_row.append('<th>' + keywords[i] + '</th>');
			}
		}
	}
	else
	{
		headers_row.append('<th></th><th></th><th></th><th>Status</th><th>Retention</th>');
		for(var i = 0; i < keywords.length; i++)
		{
			if(excluded_headers.indexOf(keywords[i]) < 0)
			{
				headers_row.append('<th>' + keywords[i] + '</th>');
			}
			
		}
	}
	
	// Make the search_results_tables sortable
	
	table.tablesorter({
		debug: false,
		headers: { 0: { sorter: false}, 1: { sorter: false}, 2: {sorter: false}, 3:{sorter: 'text'}, 4:{sorter: 'text'}, 5:{sorter: 'text'}}
	});
		
	
}

function search_data()
{
	var tab_id = selected_tab_id;
	// Save the search as latest
	
	search_request[tab_id] = {canceled: false, request: null};

	// Change the button to cancel request
	$("button.search_data", tab_id).hide();
	$("button.cancel_search", tab_id).show();
	
	// Get the table headers to use as keywords
	var table = $("table.search_results_table", tab_id);	
	var first_search = $("tbody>tr", table).length == 0;

	// Get the time range values
	var time_range = $("#time_range", tab_id);
	var start_date = get_start_date();
	if(isNaN(start_date))
	{
		alert_user("Start date is not set correctly");
		cancel_search_request();
		return false;
	}
	
	var end_date = get_end_date();
	if(isNaN(end_date))
	{
		alert_user("End date is not set correctly");
		cancel_search_request();
		return false;
	}
	
	// Check the dates are correct
	if (start_date > end_date)
	{
		alert_user("The end time needs to be later than the start time");
		cancel_search_request();
		return false;
	}
	
	start_date = new Date(start_date);
	end_date = new Date(end_date);
	
	var cadence = $("#cadence", time_range).val();
	if(cadence != '')
	{
		cadence = parseFloat(cadence.replace(",", "."));
		var unit = $("select#cadence_unit", time_range).val().toLowerCase();
		switch(unit)
		{
					case 'd':
						cadence*=24;
					case 'h':
						cadence*=60;
					case 'm':
						cadence*=60;
					case 's':
		}
	}
	else
	{
		cadence = 0;
	}
	var specific_criteria = $("div.specific_criteria  input", tab_id);
	var best_quality_only = $('[name="best_quality"]', specific_criteria);

	log("best_quality_only:", best_quality_only.value);
	var search_criteria = 
	{
		date_obs__gte: start_date.format("isoDateTime", true),
		date_obs__lte: end_date.format("isoDateTime", true),
		cadence: cadence,
	}
	// Warn the user we are making the request
	var message_box = $("p.search_message", tab_id);
	inform_user("Your search request has been sent to the server.", message_box);

	search_data_request(start_date, end_date, cadence, specific_criteria, tab_id, first_search);	

}

function search_data_request(start_date, end_date, cadence, specific_criteria, tab_id, first_search)
{
	var message_box = $("p.search_message", tab_id);
	// We test if the search request has not been canceled

	if(search_request[tab_id].canceled)
	{
		inform_user("Your search request has been canceled.", message_box);
		return;	
	}
	
	// Make the request
	search_request[tab_id].request = $.getJSON("/PMD/api/v1/" + data_series, serach_criteria,
	function(json) {
		log("Received json:", json);
		if (json.error)
		{
			if(json.results != null)
			{
				inform_user(json.error, message_box);
			}
			else
			{
				alert_user(json.error);
				alert_user(json.error, message_box);
				cancel_search_request();
			}
		}
		if(json.results)
		{
			// Display the search results
			$('div.search_results', tab_id).show();
			
			// Put the results in the table
			append_table_rows( $("table.search_results_table", tab_id), json.results, first_search);
			
			// Inform user of request progress
			var percentage = (end_slot.getTime() - start_date.getTime())/(end_date.getTime() - start_date.getTime());
			percentage = parseInt(percentage * 100);
			percentage = percentage < 10 ? '0'+percentage: percentage;
			inform_user("Displaying results " + percentage + "% done.", message_box);
			
			// Allow the user to start doing actions on the search results
			inform_user("You can now select data and use the actions button below.", $("p.results_message", tab_id));
			$('div.results_actions', tab_id).show();
			
			// Activate the clean button
			$('button.clear_results', tab_id).attr("disabled", false).removeClass('ui-button-disabled ui-state-disabled');
			
			// We update the start slot for the next request
			if(cadence <= 3600)
				start_slot = end_slot;
			else
				start_slot = new Date(start_slot.getTime() + cadence * 1000);
			
			if(start_slot < end_date) // We need to request more data
			{
				search_data_request(start_date, end_date, cadence, keywords, specific_criteria, tab_id, first_search, start_slot);
			}
			else // We finished requesting all the data
			{
				// Change the button back to search data
				$("button.cancel_search", tab_id).hide();
				$("button.search_more_data", tab_id).show();
				// Inform user that the results are ready
				inform_user("Your search request is complete.<BR/>If you make a new search, the table will be updated with the new results.<BR/>You can also clean all the results and start a new search." , message_box);
			}
			
		}
	});
}

function cancel_search_request()
{
	search_request[selected_tab_id].canceled = true;

	// Tell ajax to cancel
	if(search_request[selected_tab_id].request != null)
		search_request[selected_tab_id].request.abort();
	
	
	// Change the button back to search data
	$("button.cancel_search", selected_tab_id).hide();
	$("button.search_data", selected_tab_id).show();
	
}

function clear_search_results()
{
	// Hide the search results
	$('div.search_results', selected_tab_id).hide();
	// Remove the content of the table body
	var table = $("table.search_results_table", selected_tab_id);
	$("tbody", table).empty();
	// Remove the content of the header
	$("thead > tr", table).empty();
	// Hide the results_actions
	$('div.results_actions', selected_tab_id).hide();
	// Deactivate the clean button
	$('button.clear_results', selected_tab_id).attr('disabled', 'true').addClass('ui-button-disabled ui-state-disabled');
	// Change the button from search more to search
	$("button.search_more_data", selected_tab_id).hide();
	$("button.search_data", selected_tab_id).show();
}


function register_user(user_email)
{ 
	var email_regex = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
	if(!user_email || !email_regex.test(user_email))
	{
		return false;
	}
	else
	{
		$.cookie('email', user_email, { expires: 365, path: '/' });
		$('#user_id>button').hide();
		$('#user_id>p').text(user_email).show();
		return true;	
	}
}

function ask_user_loggin(callback)
{
	// If the user is already logged in then abort
	if($.cookie('email') && callback != null)
	{
		callback();
	}
	else
	{
		// We append the callback and show the dialog
		var dialog = $("#get_email");
		dialog.dialog('option' ,'buttons',
		{
			"Ok": function() {get_email_ok(dialog, callback);},
			"Cancel": function() {dialog.dialog("close");}
		}).dialog('open');
	}
}

function get_email_ok(dialog, callback)
{
	var user_email = $("#user_email>input", dialog).val();
	if(register_user(user_email))
	{
		
		dialog.dialog("close");
		if(callback != null)
		{
			callback();
		}	
	}
	else
	{
		$("#user_email>p", dialog).replaceWith('<p><span class="ui-icon ui-icon-alert" style="margin-right: 0.3em; float:left;"></span>Your email seems invalid, please correct it:</p>');
		dialog.removeClass("ui-state-highlight").addClass("ui-state-error");
	}
}

function get_selected_recnums(tab_id, online)
{
	var recnums = Array();
	if(online)
	{
		$("table.search_results_table tr:not(.offline) input:checked", tab_id).each(function() {recnums.push($(this).val());} );
	}
	else
	{
		$("table.search_results_table  input:checked", tab_id).each(function() {recnums.push($(this).val());} );
	}
	
	return recnums;
}
/*
function download_file(download_link, data)
{
	var location = download_link;
	if(data != null)
		location+= '?'+$.param(data);
	
	// The safest way to download a file is to open a new window (it seems Safari and IE do not like that iframe location does not refer to a non html file)
	if(download_popup != null)
		download_popup.close();
	download_popup = window.open(location, "DownloadWindow", "location=0,status=0,scrollbars=0,menubar=0,toolbar=0,width=500,height=300");
	// Test if popup has been blocked
	if (!download_popup || !download_popup.top)
	{
		alert_user("Because you have blocked popup, it is possible that the file will not download.");
		// Download the file into the hidden iframe - does not work well with safari and ie
		window.frames['download_frame'].location = location;
	}
	return true;
}
*/
function download_file(download_link, data)
{
	var location = download_link;
	if(data != null)
		location+= '?'+$.param(data);
	$("#download_frame").remove();
	$("body").append($('<iframe id="download_frame" name="download_frame" width="0px" height="0px" src="'+ location +'" />'));
}

function download_fits_file(series_name, recnum, button)
{
	var email = $.cookie('email');
	if(!email)
	{
		ask_user_loggin(function() { download_fits_file(series_name, recnum, button); });
		return false;
	}

	// Change the color of the icon so user knows what he already downloaded
	$(button).addClass('ui-button-disabled ui-state-disabled');
	
	// Download the file
	download_file(download_fits_file_link, {series_name:series_name, recnum:recnum, email:email});
}

function preview_image(series_name, recnum, button, title)
{
	var email = $.cookie('email');
	if(title == null)
		title = "Preview";
	// Change the color of the icon so user knows what he already downloaded
	$(button).addClass('ui-button-disabled ui-state-disabled');
	// Create a dialog box with a default image
	var box = $('<div class="ui-state-highlight preview_image"><img src="css/images/loading.gif"/></div>');
	box.dialog({
			modal: false,
			width: 580,
			title: title,
			draggable: true,
			resizable: true,
			close: function(event, ui) {$( this ).remove();},
	});
	// Change the image to the preview
	var image_link = '/sdodb/netdrms/get_image?label=true&color=true&upright=true&'+$.param({series_name:series_name, recnum:recnum, email:email});
	$("img", box).attr("src", image_link);
	
	// Must warn user that it is only a preview
	box.append('<p class="ui-state-error" style="margin: 1em 0;"><span class="ui-icon ui-icon-alert" style="float: left; margin-right: 0.3em;"></span>The data may differ from the preview.</p>');

}

function set_retention_dialog()
{
	var email = $.cookie('email');
	if(!email)
	{
		ask_user_loggin(function() { set_retention_dialog(); });
		return false;
	}
	var recnums = get_selected_recnums(selected_tab_id, true);
	if(recnums.length == 0)
	{
		alert_user("You must select some online records before setting the retention time.");
		return false;
	}
	else
	{
		$("#ask_retention_period").dialog('open');
	}
}

function set_retention_ok(dialog)
{
	var retention_period = parseInt($("#retention_period>input", dialog).val());
	if(isNaN(retention_period))
	{
		$("#retention_period>p", dialog).replaceWith('<p><span class="ui-icon ui-icon-alert" style="margin-right: 0.3em; float:left;"></span>Retention period invalid.<BR/>Please specify number of months:</p>');
		dialog.removeClass("ui-state-highlight").addClass("ui-state-error");
	}
	else
	{
		var recnums = get_selected_recnums(selected_tab_id, true);
		var series_name = $("div.specific_criteria>input.series_name", selected_tab_id).val();
		var warn_on_success = $("#warn_set_retention_success>input", dialog).is(':checked');
		dialog.dialog("close");
		
		// We inform the user that we sent the request
		var message_box = $('p.results_message', selected_tab_id);
		inform_user("Your request to modify the retention time has been sent to the server. Please wait for the request to terminate. The table of search results will be updated to reflect the changes.", message_box);
		
		set_retention_request(retention_period, recnums, series_name, warn_on_success, selected_tab_id);
	}
}

function set_retention_request(retention_period, recnums, series_name, warn_on_success, tab_id)
{
	// There could be nothing to request
	if(recnums != undefined && recnums.length != 0)
	{
		var message_box = $('p.results_message', tab_id);
		
		// We split the request into max_online recnums at a time
		var end_index = recnums.length < max_retention ? recnums.length : max_retention;

		$.getJSON("/sdodb/netdrms/set_retention?callback=?&",
		{
			recnum: recnums.slice(0, end_index),
			retention_period: retention_period,
			series_name: series_name,
			email: $.cookie('email')
		
		},
		function(json) {
			// We request the remaining recnums
			set_retention_request(retention_period, recnums.slice(end_index), series_name, warn_on_success, tab_id)
			
			if (json.results == null)
			{
				alert_user(json.error);
				alert_user(json.error, message_box);
			}
			else
			{
				// We inform the user how far we are into the request
				if(end_index == recnums.length)
				{
					var message = "Your request to modify the retention time of data has finished.";
					if (warn_on_success)
						inform_user(message);
				}
				else
				{
					var message = "The modification of the retention time of " + end_index + " files was requested. Please wait while we request the " + recnums.length +" remaining ones.";
				}
				if(json.error)
				{
					message += " But there was some error:<br/>"+json.error;
				}
				inform_user(message, message_box);
				
				// We update the search results table
				var table = $("table.search_results_table", tab_id);
				for(var i = 0; i < json.results.data.length; i++)
				{
					$('#'+json.results.data[i][0]+' td.retention', table).text(json.results.data[i][1]).addClass("updated").each(function(){table.trigger("updateCell",[this]);});
				}
			}
		});
	}
}



function download_data_request(series_name, recnums, tab_id)
{
	if(tab_id == null)
		tab_id = selected_tab_id;
	
	if(recnums==null)
		recnums = get_selected_recnums(tab_id, true);
	if(recnums.length == 0)
	{
		alert_user("Please select the online data to download.");
		return false;
	}
	if(recnums.length > max_zip)
	{
		alert_user("You cannot download more than " + max_zip + " files at a time.");
		return false;
	}
	if(series_name == null)
		series_name = $("div.specific_criteria>input.series_name", tab_id).val();
		
	var email = $.cookie('email');
	if(!email)
	{
		ask_user_loggin(function() { download_data_request(series_name, recnums); });
		return false;
	}
	inform_user("Your download should start shortly.<br/>We recommend you to save the zip file and to open it only when it has finished downloading completely.", $("p.results_message", tab_id));
	download_file(download_fits_file_link, {series_name:series_name, recnum:recnums, email:email});
}

function export_data(series_name, recnums, tab_id)
{
	if(tab_id == null)
		tab_id = selected_tab_id;
	
	if(recnums==null)
		recnums = get_selected_recnums(tab_id, true);
	if(recnums.length == 0)
	{
		alert_user("Please select the online data to export.");
		return false;
	}
	if(series_name == null)
		series_name = $("div.specific_criteria>input.series_name", tab_id).val();
		
	var email = $.cookie('email');
	if(!email)
	{
		ask_user_loggin(function() { export_data_request(series_name, recnums, tab_id); });
		return false;
	}
	
	// We inform the user that we sent the request
	var message_box = $('p.results_message', tab_id);
	inform_user("Your request to export data was sent to the server.", message_box);
	
	export_data_request(series_name, recnums, tab_id)
}

function export_data_request(series_name, recnums, tab_id, request_date)
{
	// There could be nothing to request
	if(recnums != undefined && recnums.length != 0)
	{
		var message_box = $('p.results_message', tab_id);
		
		// The request_id is the dircetory that will be used to store the exported data 
		if(! request_date)
		{
			var now = new Date();
			request_date = String(now.getFullYear() * 10000 + (now.getMonth() + 1) * 100 + now.getDate()) + "_" + String(now.getHours() * 10000 + now.getMinutes() * 100 + now.getSeconds());
		}
		// We split the request into max_online recnums at a time
		var end_index = recnums.length < max_export ? recnums.length : max_export;
		
		$.getJSON("/sdodb/netdrms/export_fits_file?callback=?&",
		{
			recnum: recnums.slice(0, end_index),
			series_name: series_name,
			email: $.cookie('email'),
			directory: request_date
		},
		function(json) {
			// We request the remaining recnums
			export_data_request(series_name, recnums.slice(end_index), tab_id, request_date)
			
			if (json.results == null)
			{
				alert_user(json.error);
				alert_user(json.error, message_box);
			}
			else
			{
				// We inform the user how far we are into the request
				if(end_index == recnums.length)
				{
					var message = json.results;
				}
				else
				{
					var message = end_index + " files were requested to be exported. Please wait while we request the " + recnums.length +" remaining ones.";
				}
				if(json.error)
				{
					message+= " But there was some error:<br/>"+json.error;
				}
				inform_user(message, message_box);
			}
		});
	}
}


function export_csv_results(series_name, recnums, keywords, tab_id)
{
	if(tab_id == null)
		tab_id = selected_tab_id;
	if(recnums==null)
		recnums = get_selected_recnums(tab_id, false);
	if(recnums.length == 0)
	{
		alert_user("Please select the online data to download.");
		return false;
	}
	if(series_name == null)
		series_name = $("div.specific_criteria>input.series_name", tab_id).val();
	if(keywords === null)
		keywords = get_table_headers("table.search_results_table", tab_id);
	var email = $.cookie('email');
	
	inform_user("Your download should start shortly.<br/>You can open csv files into any spreadsheet editor.", $("p.results_message", tab_id));
	download_file(export_csv_link, {series_name:series_name, recnums:recnums, keywords: keywords, email:email});
}

function bring_online(series_name, recnums, tab_id)
{
	if(tab_id == null)
		tab_id = selected_tab_id;
	if(recnums==null)
		recnums = get_selected_recnums(tab_id, false);
	if(recnums.length == 0)
	{
		alert_user("Please select the data to bring online at ROB.");
		return false;
	}
	if(series_name == null)
		series_name = $("div.specific_criteria>input.series_name", tab_id).val();
	var email = $.cookie('email');
	if(!email)
	{
		ask_user_loggin(function(){ bring_online_request(series_name, recnums, tab_id); });
		return false;
	}
	// We inform the user that we sent the request
	var message_box = $('p.results_message', tab_id);
	inform_user("Your request to make data online at ROB was sent to the server. Please wait for the request to terminate. The table of search results will be updated to reflect the changes.", message_box);
	
	bring_online_request(series_name, recnums, tab_id);
}

function bring_online_request(series_name, recnums, tab_id)
{
	// There could be nothing to request
	if(recnums != undefined && recnums.length != 0)
	{
		var message_box = $('p.results_message', tab_id);
		
		// We split the request into max_online recnums at a time
		var end_index = recnums.length < max_online ? recnums.length : max_online;
		$.getJSON("/sdodb/netdrms/bring_online?callback=?&",
		{
			recnum: recnums.slice(0, end_index),
			series_name: series_name,
			email: $.cookie('email')
		},
		function(json) {
			// We request the remaining recnums (before or after updating the table?)
			bring_online_request(series_name, recnums.slice(end_index), tab_id);
			
			if (json.results == null)
			{
				alert_user(json.error);
				alert_user(json.error, message_box);
			}
			else
			{
				// We inform the user how far we are into the request
				if(end_index == recnums.length)
				{
					var message = "Your request to bring data online at ROB has finished. It takes a few minutes per file to be available, please check back later.";
				}
				else
				{
					var message = end_index + " files were requested to be brought online at ROB. Please wait while we request the " + recnums.length +" remaining ones.";
				}
				if(json.error)
				{
					message += " But there was some error:<br/>"+json.error;
				}
				inform_user(message, message_box);
			
				// We update the search results table
				var table = $("table.search_results_table", tab_id);
				for(var i = 0; i < json.results.data.length; i++)
				{
					var recnum = json.results.data[i][0];
					var online = json.results.data[i][1];
					var retention = json.results.data[i][2];
					var row = $('#'+recnum, table);
					// If data has been brought online immediately, we need to update the row
					if(online)
					{
						// We change the state to online
						row.removeClass("offline").addClass("online");
						// And display the per record buttons
						$("td.preview>button", row).show();
						$("td.download>button", row).show();
						// Third elem of the table is Online/Offline
						$("td.status", row).text('online').addClass('updated').each(function(){table.trigger("updateCell",[this]);});
						// Fourth is retention
						$("td.retention", row).text(retention).each(function(){table.trigger("updateCell",[this]);});
					}
					else // We just show that it was requested
					{
						$('td.status', row).text("requested").addClass("updated").each(function(){table.trigger("updateCell",[this]);});
					}
				}
			}
		});
	}
}

// For futur implementation of the cutout
function update_img(self, series_name, recnum)
{
	//This is for test only
	recnum = parseInt(recnum);
	recnum %= 3;
	var img_src = "images/sun_"+recnum+".jpg";
	var dialog = $("#download_cutout");
	$("ul li", dialog).removeClass("selected");
	$(self).addClass("selected");
	$("img", dialog).attr("src", img_src);
}

function cutout_dialog(series_name, selected)
{
	if(series_name == null)
		series_name = $("div.specific_criteria>input.series_name", selected_tab_id).val();
	if(selected == null)
	{
		selected = Array();
		$("table.search_results_table tr", selected_tab_id).each(function() {
			if($("input:checked", this).length > 0)
			{
				selected.push({recnum:this.id, name:$("td:eq(5)", this).text()});
			}
		});
	}
	if(selected.length == 0)
	{
		alert_user("You must select some records before downloading a cutout.");
		return false;
	}
	if(! $.cookie('email'))
	{
		ask_user_loggin(function() { cutout_dialog(series_name, selected); });
		return false;
	}
	
	var img_list = $("#download_cutout ul");
	img_list.empty();
	for(var i = 0; i < selected.length; i++)
	{
		img_list.append('<li onclick="update_img(this,&quot;'+series_name+'&quot;,&quot;'+selected[i].recnum+'&quot;);">'+selected[i].name+'</li>');
	}
	$("li:first", img_list).click();
	$("#download_cutout").dialog("open");
}



function load_events_handlers()
{
	// Create artificial console log
	if(debug)
	{
		$(document.body).append('<div id="debug_console" style="width:50em; border: 2px solid red; position: absolute; right: 0; bottom:0;vertical-align: bottom;"></div>');
	}
	
	// Attach tabs handler
	$('#tabs').tabs(
		{
			beforeActivate: function(event, ui) {selected_tab_id = '#'+ui.newPanel.attr('id'); $(selected_tab_id).prepend($("#time_range"));}
		}
	);
	
	// Move time_range form into selected tab
	$(selected_tab_id).prepend($("#time_range"));

	// Initialise and attach datetime picker to start_date
	var now = new Date();
	var aweekago = new Date(now.getTime() - (24*3600*1000 * 7));
	
	$("#id_start_date").val(aweekago.format("isoDateTime", true));
	$("#id_start_date_picker").datetimepicker(
		{
			altField: '#id_start_date',
			altFormat: "yy-mm-dd",
			altSeparator: 'T',
			altFieldTimeOnly : false,
			hourGrid: 4,
			minuteGrid: 10,
			timeFormat: 'HH:mm:ss',
			showSecond: false,
			changeYear: true,
			changeMonth: true,
			dateFormat: 'yy-mm-dd',
			minDateTime: new Date(2010,03,01),
			maxDateTime: now,
		}
	);
	
	// Initialise and attach datetime picker to end_date
	aweekago.setTime(aweekago.getTime()+(3600*1000));
	$("#id_end_date").val(aweekago.format("isoDateTime", true));
	$("#id_end_date_picker").datetimepicker(
		{
			altField: '#id_end_date',
			altFormat: "yy-mm-dd",
			altSeparator: 'T',
			altFieldTimeOnly : false,
			hourGrid: 4,
			minuteGrid: 10,
			timeFormat: 'HH:mm:ss',
			showSecond: false,
			changeYear: true,
			changeMonth: true,
			dateFormat: 'yy-mm-dd',
			minDateTime: new Date(2010,03,01),
			maxDateTime: now,

		}
	);
	
	// Make up the buttons
	$("button.help").button({icons: {primary: "ui-icon-help"}, text:false}).addClass('ui-state-highlight').click(function(e){inform_user($(this).attr('title'))});
	$("button.select_all").button({icons: {primary: "ui-icon-check"}, text:false});
	$("button.unselect_all").button({icons: {primary: "ui-icon-close"}, text:false});
	$("button.inverse_selection").button({icons: {primary: "ui-icon-shuffle"}, text:false});
	$("button.search_data").button({icons: {primary: "ui-icon-search"}});
	$("button.cancel_search").button({icons: {primary: "ui-icon-cancel"}}).hide().addClass(".ui-state-error");
	$("button.bring_online").button({icons: {primary: "ui-icon-home"}});

	// Set first search message
	$("p.search_message").each(function(){


		inform_user("Please be aware that SDO generates large amount of data (2400 images/hour for AIA). Large searches can slow down or even crash your web browser. So please limit the time range and narrow it to what you really need.", $(this))
	});
	
	// Set some css classes
	$("div.form_section").addClass("ui-widget ui-widget-content ui-corner-all");
	$("p.form_section_title").addClass("ui-widget-header ui-corner-all ui-helper-clearfix");
	
	
	// Create the dialogs

	
	// Ask retention period dialog
	$("#ask_retention_period").dialog({
		autoOpen: false,
		width: 500,
		buttons: {
			"Set retention": function() {
				set_retention_ok($(this));
			},
			"Cancel": function() {
				$(this).dialog("close");
			}
		},
		modal: true,
		resizable: false
	}).show();
	
	
	
	// If the user is logged in we hide the log_in button and show the name, or vis versa
	var email = $.cookie('email');
	if(!email)
	{
		$('#user_id>button').button({icons: {primary: "ui-icon-person"}}).show();
	}
	else
	{
		$('#user_id>p').text(email).show();
	}

	
	// Move the table header on top of table 
	$("table.search_results_table").scroll(function(){
			var table = $(this);
			$("thead", table).css("top", table.scrollTop()+'px');
	});
		
}
// We attach all the events handler 
$(document).ready(load_events_handlers);
	
