/*
TODO
*/

// Global variables
debug = true;
selections = {};
latest_search_request = {};
username = USERNAME;

// Set implementation
var Set = function() {};
Set.prototype.add = function(o) { this[o] = true; };
Set.prototype.remove = function(o) { delete this[o]; };
Set.prototype.values = function() { return Object.keys(this); };

// Logging function, log to console if available, else log to overlay
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
		if(typeof console === "undefined")
		{		
			$("#debug_console").append('<p style="margin-top:1em;">'+message+'</p>');
		}
		else
		{
			console.log(message);
		}
	}
}

// Display a pop up with an error message or write it to the box if provided.
function alert_user(message, box)
{
	log("alert_user message: ", message);
	if(box == null)
	{
		box = $('<div><span class="ui-icon ui-icon-alert" style="float: left; margin-right: 0.3em;">Alert:</span>' + message + '</div>');
		box.dialog({
			modal: true,
			draggable: false,
			title: "Error",
			resizable: false,
			width: "auto",
			dialogClass: "ui-state-error dialog_box",
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

// Display a pop up with a informational message or write it to the box if provided
function inform_user(message, box)
{
	log("inform_user message: ", message);
	if(box == null)
	{
		box = $('<div><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Info:</span>' + message + '</div>');
		box.dialog({
			modal: false,
			draggable: false,
			title: "Note",
			resizable: false,
			width: "auto",
			dialogClass: "ui-state-highlight dialog_box",
			buttons: [
				{
					text: "Ok",
					click: function() {
						$( this ).dialog( "close" );
					}
				}
			]
		});
		//box.remove();
	}
	else
	{
		box.removeClass("ui-state-error").addClass("ui-state-highlight");
		box.html('<p><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Note:</span>' + message + '</p>').effect("highlight", {}, 2000);
	}
}

// Retrieve the data series name for any object
function get_data_series_name(object)
{
	return $(object).closest("div.tab_content").attr("id");
}

// Select all checkboxes in a table and update the selection
function select_all(table, selection)
{
	log("select_all");
	$("input:checkbox", table).each(function(){$(this).prop('checked', true);});
	selection.all_selected = true;
	selection.selected = new Set();
}

// De-select all checkboxes in a table and update the selection
function unselect_all(table, selection)
{
	log("unselect_all");
	$("input:checkbox", table).each(function(){$(this).prop('checked', false);});
	selection.all_selected = false;
	selection.selected = new Set();
}

// Update selection from selected checkboxes in a table
function update_selection_from_table(table, selection)
{
	if(selection.all_selected)
	{
		$("input:checkbox:not(:checked)", table).each(function(){selection.selected.add(this.value);});
	}
	else
	{
		$("input:checkbox:checked", table).each(function(){selection.selected.add(this.value);});
	}
}

// Select checkboxes in a table from the selection
function update_table_from_selection(table, selection)
{
	if(selection.all_selected)
	{
		$("input:checkbox", table).prop("checked", true).each(function(){
			if(this.value in selection.selected)
			{
				$(this).prop("checked", false);
			}
		});
	}
	else // Do the opposite
	{
		$("input:checkbox", table).prop("checked", false).each(function(){
			if(this.value in selection.selected)
			{
				$(this).prop("checked", true);
			}
		});
	}
}

// Make an ajax request to table_url and load the search results to section content
function load_search_result_table(section, table_url)
{
	var data_series_name = get_data_series_name(section);
	log("load_search_result_table url: ", table_url, "data_series_name: ", data_series_name);
	
	// Abort the last search request in case it is still running
	if(latest_search_request[data_series_name] !== undefined)
	{
		log("Aborting latest search request: ", latest_search_request[data_series_name].uid);
		latest_search_request[data_series_name].abort();
		latest_search_request[data_series_name] = undefined;
	}
	
	// Make the request and save it
	var request = latest_search_request[data_series_name] = $.get(table_url);
	
	// For clearer logging
	request.uid = data_series_name + " - " +(new Date()).toJSON();
	
	// Success
	request.done(function(response){
		log("load_search_result_table SUCCEEDED for request: ", request.uid);
		
		// If the request that is "done" is not the latest one, the search result section will not be updated with the received search result table
		if(latest_search_request[data_series_name] == request)
		{
			log("Updating search result section for data series: ", data_series_name, "Request matches latest search request : ", request.uid, latest_search_request[data_series_name].uid);
			
			$("div.section_content", section).html(response);
			post_load_search_result_table(section);
			$("div.section_title span.visual_indicator", section).removeClass('ui-icon-loading ui-icon-alert').addClass('ui-icon-check').attr("title", "Table has been updated");
		}
		else
		{
			log("NOT Updating search result section for data series: ", data_series_name, "Request does NOT match latest search request : ", request.uid, latest_search_request[data_series_name].uid);
		}
	});
	
	// Failure or abort
	request.fail(function(request, status){
		log("load_search_result_table FAILED for request: ", request.uid, "status: ", status, "response: ", request.responseText);
		if (status == "abort")
		{
			inform_user("Your previous search for data series "+ data_series_name + " was aborted!");
			$("div.section_title span.visual_indicator", section).removeClass('ui-icon-loading ui-icon-check').addClass('ui-icon-alert').attr("title", "Previous search was aborted");
		}
		else
		{
			alert_user(request.responseText);
			$("div.section_title span.visual_indicator", section).removeClass('ui-icon-loading ui-icon-check').addClass('ui-icon-alert').attr("title", "Table has NOT been updated");
		}
	});
	
	// Add a visual indication that the search request was submited
	$("div.section_title span.visual_indicator", section).removeClass('ui-icon-check ui-icon-alert').addClass('ui-icon-loading').attr("title", "Table is being updated");
	
}

// Set-up the section after the load
function post_load_search_result_table(section)
{
	var data_series_name = get_data_series_name(section);
	log("post_load_search_result_table data_series_name: ", data_series_name);
	
	// Transform download_data anchors to button
	$('a.download_data', section).button({icons: {primary: "ui-icon-arrowthickstop-1-s"}, text:false}).click(function(e){
		// Change the color of the icon so user knows what he already downloaded
		$(this).addClass('ui-button-disabled ui-state-disabled');
	});
	
	// Transform preview_data anchors to button
	$('a.preview_data', section).button({icons: {primary: "ui-icon-image"}, text:false}).click(function(e){
		e.preventDefault();
		preview_data($(this), $(this).attr("href"), $(this).attr("img_title"));
	});
	
	// Transform navigation anchors to buttons
	$('a.first_page', section).button({icons: {primary: "ui-icon-seek-first"}, text:false});
	$('a.previous_page', section).button({icons: {primary: "ui-icon-seek-prev"}, text:false});
	$('a.next_page', section).button({icons: {primary: "ui-icon-seek-next"}, text:false});
	$('a.last_page', section).button({icons: {primary: "ui-icon-seek-end"}, text:false});
	
	// Attach navigation buttons click handler
	var selection = selections[data_series_name];
	$('div.page_navigation a', section).each(function(){
		if($(this).attr("href")) 
		{
			$(this).click(function(e){
				e.preventDefault();
				// We update the selection
				update_selection_from_table($('table.search_result_table', section), selection);
				
				// We get the new search result table
				load_search_result_table(section, $(this).attr("href"));
			});
		}
		else
		{
			$(this).addClass('ui-button-disabled ui-state-disabled');
		}
	});
	
	// Attach select_all unselect_all buttons click handler
	$('button.select_all', section).button({icons: {primary: "ui-icon-check"}, text:true}).click(function(e){
		select_all($('table.search_result_table', section), selection);
	});
	$('button.unselect_all', section).button({icons: {primary: "ui-icon-close"}, text:true}).click(function(e){
		unselect_all($('table.search_result_table', section), selection);
	});
	
	// Mark as checked the checkboxes from previous selection
	update_table_from_selection($("table.search_result_table", section), selection);
}

function preview_data(button, image_link, title)
{
	// Change the color of the icon so user knows what he already downloaded
	button.addClass('ui-button-disabled ui-state-disabled');

	// Create a dialog box with a default loading image (while the real while is being created)
	var box = $('<div class="preview_data"><img src="' + LOADING_IMAGE_URL + '"/><p>Preview images are generated on the fly, please be patient.</p></div>');
	box.dialog({
			modal: false,
			width: 580,
			title: title || button.attr("title"),
			draggable: true,
			resizable: true,
			dialogClass: "ui-state-highlight",
			close: function(event, ui) {
				$( this ).remove(); button.removeClass('ui-button-disabled ui-state-disabled');
			},
	});

	// Change the image to the preview. The image switch will append automatically when the good image is available.
	$("img", box).attr("src", image_link);
}

// Make an ajax request to action_url and display the response
function execute_search_result_action(action_url, data, button)
{
	log("execute_search_result_action url: ", action_url, "data: ", $.param(data));
	
	// Add visual indication that the search is sent, we will restore the button after the request
	var original_icon = $("span.ui-icon", button).attr("class");
	$("span.ui-icon", button).attr("class", "ui-button-icon-primary ui-icon ui-icon-loading");
	
	$.post(action_url, data)
	.done(function(response){
		log("execute_search_result_action SUCCEEDED url: ", action_url, "response: ", response);
		$("span.ui-icon", button).attr("class", original_icon);
		inform_user(response);
	})
	.fail(function(request, status){
		log("execute_search_result_action FAILED url: ", action_url, "response: ", request.responseText);
		$("span.ui-icon", button).attr("class", original_icon);
		alert_user(request.responseText);
	});
}

// Make an ajax request to table_url and insert the result into the section content
function load_user_request_table(section, table_url, post_load_user_request_table)
{
	log("load_user_request_table url: ", table_url, "section: ", $("div.section_title", section).text());
	
	// Make the request and save it
	var request = $.get(table_url);
	
	// For clearer logging
	request.uid = (new Date()).toJSON();
	
	// Success
	request.done(function(response){
		log("load_user_request_table SUCCEEDED for request: ", request.uid);
		$("div.section_content", section).html(response);
				
		if(post_load_user_request_table !== undefined)
		{
			// Make the section pretty
			post_load_user_request_table(section);
		}
	});
	
	// Failure or abort
	request.fail(function(request, status){
		log("load_user_request_table FAILED for request: ", request.uid, "status: ", status, "response: ", request.responseText);
		alert_user(request.responseText);
	});
}

// Set-up the section after the load
function post_load_user_request_table(section)
{
	log("post_load_user_request_table section: ", $("div.section_title", section).text());
	
	// Transform open ftp location anchor to button
	$('div.section_content a.open_ftp_location', section).button({icons: {primary: "ui-icon-folder-open"}, text:false});
	
	// Transform delete request anchors to button
	$('div.section_content a.delete_request', section).button({icons: {primary: "ui-icon-trash"}, text:false}).click(function(e){
		var anchor = $(this);
		log("delete_request url: ", anchor.attr("href"));
		e.preventDefault();
		// Call a delete on the request
		var request = $.ajax({
			url: anchor.attr("href"),
			type: 'DELETE'
		});
		
		request.done(function(response){
			log("delete_request SUCCEEDED for request: ", request.uid, "status: ", status, "response: ", response);
			// Remove the row from the table
			anchor.closest("tr").remove();
		});
		
		request.fail(function(request, status){
			log("delete_request FAILED for request: ", request.uid, "status: ", status, "response: ", request.responseText);
			alert_user(request.responseText);
		});
	});
}

// Load all request tables in the user tab
function load_user_tab_content()
{
	// Load the export data request table
	load_user_request_table($("div#export_data_request_section"), EXPORT_DATA_REQUEST_TABLE_URL, post_load_user_request_table);
	// Load the export meta-data request table
	load_user_request_table($("div#export_metadata_request_section"), EXPORT_METADATA_REQUEST_TABLE_URL, post_load_user_request_table);

}

// Things to do at the very beginning
function load_events_handlers()
{
	// Create artificial console log
	if(debug && typeof console === "undefined")
	{
		$(document.body).append('<div id="debug_console" style="width:50em; border: 2px solid red; position: absolute; right: 0; bottom:0;vertical-align: bottom;"></div>');
	}
	
	// Attach tabs handler
	$("#tabs").tabs(
		{
			active: 0,
			beforeActivate: function(event, ui){
				if(ui.newPanel.attr('id') == "user" && username)
				{
					load_user_tab_content();
				}
			}
		}
	);
	
	// Set defaults for all datetime pickers
	$.datepicker.setDefaults(
		{
			buttonImage: CALENDAR_IMAGE_URL,
			buttonImageOnly: true,
			buttonText: "Click to open date picker",
			showOn: "button",
			changeYear: true,
			changeMonth: true,
			dateFormat: 'yy-mm-dd',
		}
	);
	
	// Attach datetime picker to start_date and end_date
	$("input.date_time_input").datetimepicker(
		{
			minDateTime: new Date(2010,02,29),
			maxDateTime: new Date(),
			// time picker options cannot be set trough setDefaults
			timeFormat: 'HH:mm:ss', 
			hourGrid: 6,
			minuteGrid: 10,
			showSecond: false,
		}
	);
	
	// Transform the login form to do ajax request instead
	$("form#login_form").submit(function(e){
		e.preventDefault();
		var form = $(e.target);
		log("submit form action: ", form.attr("action"), "query: ", form.serialize());
		
$.post(form.attr("action"), form.serialize())
		.done(function(response){
			log("login SUCCEEDED response: ", response);
			// TODO load request and logout button
			username = response;
			// Change tab name to username
			$("li#user_tab>a").html("<span class='ui-icon ui-icon-person visual_indicator'></span>" + username); 
			// Remove login form
			$("form#login_form").remove();
			// Show all hidden content
			$("div#user > *").show("fast");
			// Load the request tables
			load_user_tab_content()
		})
		.fail(function(request, status){
			log("login FAILED response: ", request.responseText);
			alert_user(request.responseText);
		});
	});	
	
	// Transform the search form to do ajax request instead
	$("form.data_search_form").submit(function(e){
		e.preventDefault();
		var form = $(e.target);
		
		// Update the selection
		var selection = selections[get_data_series_name(e.target)];
		selection.all_selected = false;
		selection.selected = new Set();
		selection.search_query = form.serialize();
		
		// Make the search and load the table
		load_search_result_table($("div.search_result_section", form.closest("div.tab_content")), form.attr("action") + "?" + form.serialize());
	});
	
	// Change helptext into buttons
	$("span.helptext").replaceWith(function() {return "<button type='button' class='help small_button' title='" + $(this).text() + "'>Help</button>";});
	
	$("button.help").button({icons: {primary: "ui-icon-help"}, text:false}).addClass('ui-state-highlight').click(function(e){
		inform_user($(this).attr("title"));
	});
	
	// Make up the action buttons
	$("button.search_data").button({icons: {primary: "ui-icon-search"}});
	$("button.download_bundle").button({icons: {primary: "ui-icon-cart"}}).hide();
	$("button.export_data").button({icons: {primary: "ui-icon-extlink"}});
	$("button.export_metadata").button({icons: {primary: "ui-icon-document"}});
	$("button.export_cutout").button({icons: {primary: "ui-icon-scissors"}}).hide();
	
	// When user make an export request, check that he is logged in first
	$("div.search_result_actions button").click(function(e){
		log("click handler for button: ", $(e.target).text())
		if(! username)
		{
			e.preventDefault();
			// If user is not logged in, ask him to do so
			inform_user("Please, login before making an export request.");
			
			// Open the login tab
			$("#tabs").tabs("option", "active" , -1);
		}
	});
	
	$("button#login").button({icons: {primary: "ui-icon-key"}, text:true});
	$("a#logout").button({icons: {primary: "ui-icon-extlink"}, text:true});
	
	// Transform the search result action form to do ajax request instead
	$("div.search_result_actions form").submit(function(e){
		e.preventDefault();

		// Update the selection with the selected checkboxes
		var selection = selections[get_data_series_name(e.target)];
		update_selection_from_table($('div.search_result_section table.search_result_table', $(e.target).closest("div.search_result_panel")), selection);
		
		// Create the data object to be sent
		var data = {
			all_selected: selection.all_selected,
			selected: selection.selected.values(),
		};
		execute_search_result_action($(e.target).attr("action")+ "?" + selection.search_query, data, $("button", e.target));
	});
	
	// Set up global variables
	$("div.tab_content").each(function(){
		selections[this.id] = {
			all_selected: false,
			selected: new Set(),
			search_query: undefined,
		};
	});

	// Set some JQuery classes to make sections pretty
	$("div.section").addClass("ui-widget ui-widget-content ui-corner-all");
	$("div.section_title, div.actions").addClass("ui-widget-header ui-corner-all ui-helper-clearfix");
	
	// Some adjustments to ajax requests (get and post) to make it run smoothly with django
	$.ajaxSetup({
		// Include the crsf token to all ajax post
		beforeSend: function(xhr, settings) {
			if (!/^https?:.*/.test(settings.url) && settings.type != "GET")
			{
				xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
			}
		},
		// Transform the data to be sent in a traditional way so that django can read it  
		traditional: true,
	});
	
	// Submit the search forms as to show some data in the tables from the beginning
  $("form.data_search_form").submit();
}


// Attach all the events handler 
$(document).ready(load_events_handlers);
