/*
TODO
Improve the download
*/

// Global variables
selected_tab_id = null;
search_request = {};
download_popup = null;
debug = true;

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

// Things to do at the very beggining
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
			active: -1,
			heightStyle: "fill",
			beforeActivate: function(event, ui) {selected_tab_id = $('#'+ui.newPanel.attr('id')); log("Prepending time_range panel to:", selected_tab_id.attr('id')); selected_tab_id.prepend($("#time_range"));}
		}
	);
	
	// Move time_range form into selected tab
	$( "#tabs" ).tabs( "option", "active" , 0);
	log("selected_tab_id:", selected_tab_id.attr('id'));
	//$(selected_tab_id).prepend($("#time_range"));

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
	
	// change helptext into buttons
	$("span.helptext").replaceWith(function() {return '<button class="help" title="' + $(this).text() + '">Help</button>';});
	
	// Make up the buttons
	$("button.help").button({icons: {primary: "ui-icon-help"}, text:false}).addClass('ui-state-highlight').click(function(e){inform_user($(this).attr('title'))});
	$("button.select_all").button({icons: {primary: "ui-icon-check"}, text:false});
	$("button.unselect_all").button({icons: {primary: "ui-icon-close"}, text:false});
	$("button.inverse_selection").button({icons: {primary: "ui-icon-shuffle"}, text:false});
	$("button.search_data").button({icons: {primary: "ui-icon-search"}});
	$("button.cancel_search").button({icons: {primary: "ui-icon-cancel"}}).hide().addClass(".ui-state-error");
	$("button.bring_online").button({icons: {primary: "ui-icon-home"}});

	
	// Set some css classes
	$("div.form_section").addClass("ui-widget ui-widget-content ui-corner-all");
	$("div.form_section_title").addClass("ui-widget-header ui-corner-all ui-helper-clearfix");
	
	
	// Move the table header on top of table 
	$("table.search_results_table").scroll(function(){
			var table = $(this);
			$("thead", table).css("top", table.scrollTop()+'px');
	});
		
}
// We attach all the events handler 
$(document).ready(load_events_handlers);
	
