/*
TODO
Improve the download
*/

// Global variables
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
	log("alert user", message);
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
	log("inform user", message);
	if(box == null)
	{
		box = $('<div class="ui-state-highlight"><span class="ui-icon ui-icon-info" style="float: left; margin-right: 0.3em;">Note:</span>' + message + '</div>');
		box.dialog({
			modal: false,
			draggable: false,
			title: "Note",
			resizable: false,
			//close: function(event, ui) {$( this ).remove();},
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

function get_start_date()
{
	return Date.parse($("#id_start_date").val());
}

function get_end_date()
{
	return Date.parse($("#id_end_date").val());
}


function select_all(context)
{
	log("select_all");
	var check_boxes = $("input:checkbox", context);
	check_boxes.each(function(){$(this).attr('checked', true)});
}

function unselect_all(context)
{
	log("unselect_all");
	var check_boxes = $("input:checkbox", context);
	check_boxes.each(function(){$(this).attr('checked', false)});
}

function load_result_table(params, query)
{
	log("load_result_table", params, query);
	params = $.parseJSON(params);
	var get_url = params.url + "?page=" + params.page;
	if(query !== undefined)
	{	
		get_url += "&" + query;
	}
	
	var section_content = $("div.search_results>div.section_content", $("#"+params.data_series));
	log("load_result_table sending request url", get_url);
	section_content.load(get_url, function(response, status, xhr){
		log("load_result_table request status", status);
		if(status == "success")
		{
			post_load_result_table(section_content);
		}
		else
		{
			alert_user(response);
		}
	});
}

function post_load_result_table(section_content)
{
	log("post_load_result_table");
	$('button.download_fits', section_content).button({icons: {primary: "ui-icon-arrowthickstop-1-s"}, text:false});
	$('button.preview_image', section_content).button({icons: {primary: "ui-icon-image"}, text:false});
	$('button.first_page', section_content).button({icons: {primary: "ui-icon-seek-first"}, text:false}).click(function(e){
		load_result_table($(this).attr("params"));
	});
	$('button.previous_page', section_content).button({icons: {primary: "ui-icon-seek-prev"}, text:false}).click(function(e){
		load_result_table($(this).attr("params"));
	});
	$('button.next_page', section_content).button({icons: {primary: "ui-icon-seek-next"}, text:false}).click(function(e){
		load_result_table($(this).attr("params"));
	});
	$('button.last_page', section_content).button({icons: {primary: "ui-icon-seek-end"}, text:false}).click(function(e){
		load_result_table($(this).attr("params"));
	});
	$('button.select_all', section_content).button({icons: {primary: "ui-icon-check"}, text:true}).click(function(e){
		select_all($('table.result_table', section_content));
	});
	$('button.unselect_all', section_content).button({icons: {primary: "ui-icon-close"}, text:true}).click(function(e){
		unselect_all($('table.result_table', section_content));
	});
	// Check if selected_all or selected is not empty, and set as selected
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
	$('#tabs').tabs(
		{
			active: -1,
			heightStyle: "fill",
			beforeActivate: function(event, ui){
				if(ui.newPanel.attr('id') != "user")
				{
					var selected_tab = $('#'+ui.newPanel.attr('id'));
					log("Prepending time_range panel to:", selected_tab.attr('id'));
					$("form", selected_tab).prepend($("#time_range"));
				}				
			}
		}
	);
	
	// Move time_range form into selected tab
	$( "#tabs" ).tabs( "option", "active" , 0);
	
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
			minDateTime: new Date(2010,03,01),
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
			minDateTime: new Date(2010,03,01),
			maxDateTime: now,
			// time picker options cannot be set trough setDefaults
			timeFormat: 'HH:mm:ss',
			hourGrid: 6,
			minuteGrid: 10,
			showSecond: false,
		}
	);

	
	// Change helptext into buttons
	$("span.helptext").replaceWith(function() {return '<button type="button" class="help" title="' + $(this).text() + '">Help</button>';});
	
	// Make up the buttons
	$("button.help").button({icons: {primary: "ui-icon-help"}, text:false}).addClass('ui-state-highlight').click(function(e){
		inform_user($(this).attr("title"))
	});
	$("button.search_data").button({icons: {primary: "ui-icon-search"}}).click(function(e){
		e.preventDefault();
		load_result_table($(this).attr("params"), $(this).closest('form').serialize());
	});
	$("button.select_all").button({icons: {primary: "ui-icon-check"}, text:false}).click(function(e){
		select_all($(this).closest("table"));
	});
	$("button.unselect_all").button({icons: {primary: "ui-icon-close"}, text:false}).click(function(e){
		unselect_all($(this).closest("table"));
	});
	$("button.download_data").button({icons: {primary: "ui-icon-cart"}}).hide();
	$("button.export_data").button({icons: {primary: "ui-icon-extlink"}}).click(function(e){});
	$("button.export_keywords").button({icons: {primary: "ui-icon-document"}}).click(function(e){});
	$("button.bring_online").button({icons: {primary: "ui-icon-home"}}).hide();
	$("button.get_cutout").button({icons: {primary: "ui-icon-scissors"}}).hide();
	$("button#logout").button({icons: {primary: "ui-icon-extlink"}, text:true}).click(function(e){
		window.location.href=$(this).attr("href");
	});


	// Set some JQuery classes
	$("div.section").addClass("ui-widget ui-widget-content ui-corner-all");
	$("div.section_title").addClass("ui-widget-header ui-corner-all ui-helper-clearfix");
			
}
// We attach all the events handler 
$(document).ready(load_events_handlers);
	
