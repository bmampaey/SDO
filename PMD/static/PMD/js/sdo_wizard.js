/*
TODO
Improve the download
*/

// Global variables
debug = true;
selections = {};
latest_search_request = {};

// Set implementation
var Set = function() {};
Set.prototype.add = function(o) { this[o] = true; };
Set.prototype.remove = function(o) { delete this[o]; };
Set.prototype.values = function() { return Object.keys(this); };

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


function alert_user(message, box)
{
	// Display a pop up with an error message or write it to the box if provided.
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

function inform_user(message, box)
{
	// Display a pop up with a informational message or write it to the box if provided
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

function get_data_series_name(object)
{
	return $(object).closest("div.tab_content").attr("id");
}

function select_all(table)
{
	log("select_all");
	$("input:checkbox", table).each(function(){$(this).prop('checked', true);});
	var data_series_name = get_data_series_name(table);
	selections[data_series_name].all_selected = true;
	selections[data_series_name].selected = new Set();
}

function unselect_all(table)
{
	log("unselect_all");
	$("input:checkbox", table).each(function(){$(this).prop('checked', false);});
	var data_series_name = get_data_series_name(table);
	selections[data_series_name].all_selected = false;
	selections[data_series_name].selected = new Set();
}


function load_result_table(result_section, table_url)
{
	// Make an ajax request to table_url and load the result to result_section
	var data_series_name = get_data_series_name(result_section);
	log("load_result_table url: ", table_url, "data_series_name: ", data_series_name);
	
	// Abort the last search request in case it is still running
	if(latest_search_request[data_series_name] !== undefined)
	{
		log("Aborting latest search request: ", latest_search_request[data_series_name].uid);
		latest_search_request[data_series_name].abort();
		latest_search_request[data_series_name] = undefined;
	}
	
	// Make the request and save it
	var request = latest_search_request[data_series_name] = $.get(table_url);
	
	// For clearer login
	request.uid = data_series_name + " - " +(new Date()).toJSON();
	
	// Success
	request.done(function(response){
		log("load_result_table SUCCEEDED for request: ", request.uid);
		
		// If the request that is "done" is not the latest one, the result section will not be updated with the received result table
		if(latest_search_request[data_series_name] == request)
		{
			log("Updating result section for data series: ", data_series_name, "Request matches latest search request : ", request.uid, latest_search_request[data_series_name].uid);
			
			$("div.section_content", result_section).html(response);
			post_load_result_table(result_section);
			$("div.section_title span.visual_indicator", result_section).removeClass('ui-icon-loading ui-icon-alert').addClass('ui-icon-check').attr("title", "Table has been updated");
		}
		else
		{
			log("NOT Updating result section for data series: ", data_series_name, "Request does NOT match latest search request : ", request.uid, latest_search_request[data_series_name].uid);
		}
	});
	
	// Failure or abort
	request.fail(function(request, status){
		log("load_result_table FAILED for request: ", request.uid, "status: ", status, "response: ", request.responseText);
		if (status == "abort")
		{
			inform_user("Your previous search for data series "+ data_series_name + " was aborted!");
			$("div.section_title span.visual_indicator", result_section).removeClass('ui-icon-loading ui-icon-check').addClass('ui-icon-alert').attr("title", "Previous search was aborted");
		}
		else
		{
			alert_user(request.responseText);
			$("div.section_title span.visual_indicator", result_section).removeClass('ui-icon-loading ui-icon-check').addClass('ui-icon-alert').attr("title", "Table has NOT been updated");
		}
	});
	
	// Add a visual indication that the search request was submited
	$("div.section_title span.visual_indicator", result_section).removeClass('ui-icon-check ui-icon-alert').addClass('ui-icon-loading').attr("title", "Table is being updated");
	
}

function post_load_result_table(result_section)
{
		
	var data_series_name = get_data_series_name(result_section);
	log("post_load_result_table data_series_name: ", data_series_name);
	
	// Transform download anchors to button
	$('a.download_fits', result_section).button({icons: {primary: "ui-icon-arrowthickstop-1-s"}, text:false}).click(function(e){
		e.preventDefault();
		download_fits($(this), $(this).attr("href"));
	});
	
	// Transform preview anchors to button
	$('a.preview_image', result_section).button({icons: {primary: "ui-icon-image"}, text:false}).click(function(e){
		e.preventDefault();
		preview_image($(this), $(this).attr("href"), $(this).attr("img_title"));
	});
	
	// Transform navigation anchors to buttons
	$('a.first_page', result_section).button({icons: {primary: "ui-icon-seek-first"}, text:false});
	$('a.previous_page', result_section).button({icons: {primary: "ui-icon-seek-prev"}, text:false});
	$('a.next_page', result_section).button({icons: {primary: "ui-icon-seek-next"}, text:false});
	$('a.last_page', result_section).button({icons: {primary: "ui-icon-seek-end"}, text:false});
	
	// Attach navigation buttons click handler
	var selection = selections[data_series_name];
	$('div.page_navigation a', result_section).each(function(){
		if($(this).attr("href")) 
		{
			$(this).click(function(e){
				e.preventDefault();
				// We update the selection
				if(selection.all_selected)
				{
					$("input:checkbox:not(:checked)", $('table.result_table', result_section)).each(function(){selection.selected.add(this.value);});
				}
				else
				{
					$("input:checkbox:checked", $('table.result_table', result_section)).each(function(){selection.selected.add(this.value);});
				}
				// We get the new result table
				load_result_table(result_section, $(this).attr("href"));
			});
		}
		else
		{
			$(this).addClass('ui-button-disabled ui-state-disabled');
		}
	});
	// TODO create the buttons entirely in javascript and remove from result_table
	// Attach select_all unselect_all buttons click handler
	$('button.select_all', result_section).button({icons: {primary: "ui-icon-check"}, text:true}).click(function(e){
		select_all($('table.result_table', result_section));
	});
	$('button.unselect_all', result_section).button({icons: {primary: "ui-icon-close"}, text:true}).click(function(e){
		unselect_all($('table.result_table', result_section));
	});
	
	// If selected_all is set, check all checkboxes and uncheck the selected
	if(selection.all_selected)
	{
		$("table.result_table input:checkbox", result_section).prop("checked", true).each(function(){
			if(this.value in selection.selected)
			{
				$(this).prop("checked", false);
			}
		});
	}
	else // Do the opposite
	{
		$("table.result_table input:checkbox", result_section).prop("checked", false).each(function(){
			if(this.value in selection.selected)
			{
				$(this).prop("checked", true);
			}
		});
	}
}

function download_fits(button, file_link)
{
	// Change the color of the icon so user knows what he already downloaded
	button.addClass('ui-button-disabled ui-state-disabled');
	
	// Download the file
	window.location.href = file_link;
}

function preview_image(button, image_link, title)
{
	// Change the color of the icon so user knows what he already downloaded
	button.addClass('ui-button-disabled ui-state-disabled');

	// Create a dialog box with a default loading image (while the real while is being created)
	var box = $('<div class="preview_image"><img src="' + LOADING_IMAGE_URL + '"/><p>Preview images are generated on the fly, please be patient.</p></div>');
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

function execute_result_action(action_url, data)
{
	// Make an ajax request to action_url and display the response
	log("execute_result_action url: ", action_url, "data: ", $.param(data));
	$.post(action_url, data)
	.done(function(response){
		log("execute_result_action SUCCEEDED url: ", action_url, "response: ", response);
		inform_user(response);
	})
	.fail(function(request, status){
		log("execute_result_action FAILED url: ", action_url, "response: ", request.responseText);
		alert_user(request.responseText);
	});
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
			active: -1,
			beforeActivate: function(event, ui){
				if(ui.newPanel.attr('id') != "user")
				{
					var selected_tab = $('#'+ui.newPanel.attr('id'));
					log("Prepending time_range panel to:", selected_tab.attr('id'));
					$("form.data_search_form", selected_tab).prepend($("#time_range"));
				}				
			}
		}
	);
	
	// Move time_range form into selected tab
	$("#tabs").tabs( "option", "active" , 0);
	
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
	var now = new Date();
	$("#id_start_date").datetimepicker(
		{
			minDateTime: new Date(2010,03,29),
			maxDateTime: now,
			// time picker options cannot be set trough setDefaults
			timeFormat: 'HH:mm:ss', 
			hourGrid: 6,
			minuteGrid: 10,
			showSecond: false,
		}
	);
	
	$("#id_end_date").datetimepicker(
		{
			minDateTime: new Date(2010,03,29),
			maxDateTime: now,
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
		do_login(form.attr("action") + "?" + form.serialize());
	});	
	
	$("button#login").button({icons: {primary: "ui-icon-key"}, text:true});
	
	$("button#logout").button({icons: {primary: "ui-icon-extlink"}, text:true}).click(function(e){
		window.location.href = $(this).attr("href");
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
		load_result_table($("div.result_section", form.closest("div.tab_content")), form.attr("action") + "?" + form.serialize());
	});
	
	// Change helptext into buttons
	$("span.helptext").replaceWith(function() {return '<button type="button" class="help" title="' + $(this).text() + '">Help</button>';});
	
	$("button.help").button({icons: {primary: "ui-icon-help"}, text:false}).addClass('ui-state-highlight').click(function(e){
		inform_user($(this).attr("title"));
	});
	
	// Make up the action buttons and add click handler
	$("button.search_data").button({icons: {primary: "ui-icon-search"}});
	$("button.download_bundle").button({icons: {primary: "ui-icon-cart"}}).hide();
	$("button.export_data").button({icons: {primary: "ui-icon-extlink"}}).click(function(e){$(e.target).prop("disabled", true);});
	$("button.export_keywords").button({icons: {primary: "ui-icon-document"}}).click(function(e){});
	$("button.bring_online").button({icons: {primary: "ui-icon-home"}}).hide();
	$("button.export_cutout").button({icons: {primary: "ui-icon-scissors"}}).hide();
	
	
	// Transform the result action form to do ajax request instead
	$("div.result_actions form").submit(function(e){
		e.preventDefault();
		// Update the selected checkboxes
		var selection = selections[get_data_series_name(e.target)];
		if(selection.all_selected)
		{
			$("input:checkbox:not(:checked)", $('div.result_section table.result_table', $(e.target).closest("div.result_panel"))).each(function(){selection.selected.add(this.value);});
		}
		else
		{
			$("input:checkbox:checked", $('div.result_section table.result_table', $(e.target).closest("div.result_panel"))).each(function(){selection.selected.add(this.value);});
		}
		// Create the data object to be sent
		var data = {
			all_selected: selection.all_selected,
			selected: selection.selected.values(),
		};
		execute_result_action($(e.target).attr("action")+ "?" + selection.search_query, data);
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
	$("div.actions").addClass("ui-widget-content ui-corner-all ui-helper-clearfix");
	
	// Some adjustments to ajax requests (get and post) to make it run smoothly with django
	$.ajaxSetup({
		// Include the crsf token to all ajax post
		beforeSend: function(xhr, settings) {
			if (!/^https?:.*/.test(settings.url)  && settings.type == "POST")
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
