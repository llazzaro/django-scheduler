
/* TODO those function should be methods of calendar */
function weekcal_save_event($calendar, calEvent){
    /* post data to the server
     * if the server returns an error we display alert
     * and reload events to get back to original values
     * */
    start = calEvent.start;
    end = calEvent.end;
    title = calEvent.title;
    body = calEvent.body;
    st = format_datetime(start);
    en = format_datetime(end);
    data = {id:calEvent.id, start:st, end:en, title:title, description:body};
    if(calEvent.recurring == true){
        url = edit_occurrence_url;
    }else{
        url = edit_event_url;
    }
    $.post(edit_occurrence_url, data, function(data){
        if(data.error == undefined){
            evt = data[0]
            calEvent.id = evt.id;
            calEvent.recurring = evt.recurring;
            calEvent.persisted = evt.persisted;
            $calendar.weekCalendar("updateEvent", calEvent);
        }else{
            alert(e + data);
            $calendar.weekCalendar("refresh");
        }
    }, 'json');
}


function format_time(dt){
    if(dt==undefined) return '';
    return lead_zero(dt.getHours()) + ":" + lead_zero(dt.getMinutes());
}

function format_date(dt){
    if(dt==undefined) return '';
    return dt.getFullYear() + '-' + lead_zero(dt.getMonth()+1) + '-' + lead_zero(dt.getDate());
}

function parse_date(s){
    s = s.split('-');
    return new Date(parseInt(s[0]), parseInt(s[1], 10)-1, parseInt(s[2], 10));
}

function dateplustime(d, t){
    var dt = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    dt.setHours(t.getHours());
    dt.setMinutes(t.getMinutes());
    dt.setSeconds(t.getSeconds());
    return dt;
}

$(document).ready(function() {

    var $calendar = $('#calendar');

    $calendar.weekCalendar({
         /* TODO input parameters dynamically from settings */
        timeslotsPerHour : timeslotsPerHour,
        allowCalEventOverlap : allowCalEventOverlap,
        firstDayOfWeek : firstDayOfWeek,
        businessHours :businessHours,
        height : function($calendar) {
            return $(window).height() - $("h1").outerHeight();
        },
        eventRender : function(calEvent, $event) {
            if (calEvent.end.getTime() < new Date().getTime()) {
                /* past events grayed out */
                $event.attr("class", $event.attr("class") + " pastEvent");
            }
            if((calEvent.recurring) && !(calEvent.persisted)){
                /* mark those which are parts of a recurrence chain */
                $event.attr("class", $event.attr("class") + " partOfChain");
            }
            if(calEvent.readOnly){
                $event.css("cursor", "default");
            }
        },
        draggable : function(calEvent, $event) {
            return calEvent.readOnly != true;
        },
        resizable : function(calEvent, $event) {
            return calEvent.readOnly != true;
        },
        eventNew : function(calEvent, $event) {
            if(!user_is_authenticated){
                alert("You must be logged in to create events");
                $calendar.weekCalendar("removeUnsavedEvents");
                return;
            }
            var $dialogContent = $("#event_edit_container");
            resetForm($dialogContent);
            var startField = $dialogContent.find("select[name='start']").val(calEvent.start);
            var endField =  $dialogContent.find("select[name='end']").val(calEvent.end);
            var titleField = $dialogContent.find("input[name='title']");
            var bodyField = $dialogContent.find("textarea[name='body']");
            var endRecPeriodField = $dialogContent.find("input[name='end_recurring_period']").datepicker({showOn:'both', buttonText:'choose', dateFormat:'yy-mm-dd'});
            var startDateField = $dialogContent.find("input[name='start_date']").datepicker({showOn:'both', buttonText:'choose', dateFormat:'yy-mm-dd'})
            $dialogContent.find("input[name='start_date']").val(format_date(calEvent.start));

            var ruleField = $dialogContent.find("select[name='rule']")
            $dialogContent.dialog({
                modal: true,
                title: "New Calendar Event",
                close: function() {
                    $dialogContent.dialog("destroy");
                    $dialogContent.hide();
                    $('#calendar').weekCalendar("removeUnsavedEvents");
                },
                buttons: {
                    save : function(){

                        start_date = parse_date(startDateField.val());
                        start_time = new Date(startField.val());
                        start = dateplustime(start_date, start_time);
                        end_time = new Date(endField.val());
                        end = dateplustime(start_date, end_time);
                        title = titleField.val();
                        body = bodyField.val();
                        calEvent.start = start;
                        calEvent.end = end;
                        calEvent.title = title;
                        calEvent.body = body;
                        calEvent.end_recurring_period = endRecPeriodField.val()
                        calEvent.rule = ruleField.val()

                        st = format_datetime(start);
                        en = format_datetime(end);
                        data = {start:st, end:en, title:title, description:body,
                            end_recurring_period:calEvent.end_recurring_period,
                            rule:calEvent.rule};
                        $.post(edit_event_url, data, function(data){
                            if(data.error == undefined){
                                evt = data[0]
                                calEvent.id = evt.id;
                                calEvent.recurring = evt.recurring;
                                calEvent.persisted = evt.persisted;
                                if(calEvent.recurring){
                                    // we have to reload all events becase we don't
                                    // know how many occurrences there is going to be
                                    $calendar.weekCalendar("refresh");
                                }else{
                                    $calendar.weekCalendar("removeUnsavedEvents");
                                    $calendar.weekCalendar("updateEvent", calEvent);
                                }
                                $dialogContent.dialog("close");
                            }else{
                                alert(data.error);
                            }
                        }, 'json');
                    },
                    cancel : function(){
                        $dialogContent.dialog("close");
                    }
                }
            }).show();
            $dialogContent.find(".date_holder").text($calendar.weekCalendar("formatDate", calEvent.start));
            setupStartAndEndTimeFields(startField, endField, calEvent, $calendar.weekCalendar("getTimeslotTimes", calEvent.start));
            $(window).resize().resize(); //fixes a bug in modal overlay size ??
        },

        eventDrop : function(calEvent, $event) {
            weekcal_save_event($calendar, calEvent);
        },

        eventResize : function(calEvent, $event) {
            weekcal_save_event($calendar, calEvent);
        },

        eventClick : function(calEvent, $event) {
            if(calEvent.readOnly == true){
                return;
            }
            if(calEvent.recurring){
                if(calEvent.persisted){
                    editOccurrence(calEvent, $event);
                }else{
                    $("#editing_choice_dialog").dialog({
                        modal:true,
                        buttons:{
                            All:function(){
                                $("#editing_choice_dialog").dialog("destroy");
                                editEvent(calEvent, $event);
                            },
                            This:function(){
                                $("#editing_choice_dialog").dialog("destroy");
                                editOccurrence(calEvent, $event);
                            },
                            Cancel:function(){
                                $("#editing_choice_dialog").dialog("destroy");
                            }
                        }
                    }).show();
                }
            }else{
                editEvent(calEvent, $event);
            }
        },

        eventMouseover : function(calEvent, $event) {
            /* TODO: show tooltip with detailed info */
        },

        eventMouseout : function(calEvent, $event) {
        },

        noEvents : function() {
        },

        data : function(start, end, callback) {
            /* this is called (a) upon page load and (b) when week is changed
            * start and end are beginning/end of selected week */
            var url = get_week_occurrences_url + '?year=' + start.getFullYear() + '&month=' + (start.getMonth() + 1) + '&day=' + start.getDate();
            $.getJSON(url, function(data){
                res = {events:data};
                callback(res);
            });
        }
    });

    function editEvent(calEvent, $event) {
        /* TODO add an editable date field to dialog (to display/edit start date
         * of the event itself, not occurrence we clicked! */
        var $dialogContent = $("#event_edit_container");
        resetForm($dialogContent);
        var url = get_event_url + '?event_id=' + calEvent.event_id;
        $.getJSON(url, function(data){
            calEvent = data[0];
            var startField = $dialogContent.find("select[name='start']");
            var endField =  $dialogContent.find("select[name='end']");
            var startDateField = $dialogContent.find("input[name='start_date']")
            var titleField = $dialogContent.find("input[name='title']").val(calEvent.title);
            var bodyField = $dialogContent.find("textarea[name='body']").val(calEvent.body);
            var endRecPeriodField = $dialogContent.find("input[name='end_recurring_period']");
            var ruleField = $dialogContent.find("select[name='rule']").val(calEvent.rule);

            $dialogContent.dialog({
                modal: true,
                title: "Edit - " + calEvent.title,
                close: function() {
                    $dialogContent.dialog("destroy");
                    $dialogContent.hide();
                    $('#calendar').weekCalendar("removeUnsavedEvents");
                },
                buttons: {
                save : function(){
                    /* send new data to the server; if response is OK
                    * then update calendar and close dialog */
                    start_time = new Date(startField.val());
                    end_time = new Date(endField.val());
                    start_date = parse_date(startDateField.val());
                    start = dateplustime(start_date, start_time);
                    end = dateplustime(start_date, end_time);
                    title = titleField.val();
                    body = bodyField.val();
                    st = format_datetime(start);
                    en = format_datetime(end);
                    end_recurring_period = endRecPeriodField.val();
                    rule = ruleField.val()
                    data = {id:calEvent.id, start:st, end:en, title:title, description:body,
                        end_recurring_period:end_recurring_period, rule:rule};
                    $.post(edit_event_url, data, function(data){
                        if(data.error == undefined){
                            $calendar.weekCalendar("refresh");
                            $dialogContent.dialog("close");
                        }else{
                            alert(data.error);
                        }
                    }, 'json');
                    },
                    "delete" : function(){
                        data = {id:calEvent.id, action:"cancel"};
                        $.post(edit_event_url, data, function(data){
                            if(data.error == undefined){
                                $calendar.weekCalendar("refresh");
                                $dialogContent.dialog("close");
                            }else{
                                alert(data.error);
                            }
                        });
                    },
                    cancel : function(){
                        $dialogContent.dialog("close");
                    }
                }
            }).show();

            startDateField.datepicker({showOn:'both', buttonText:'choose', dateFormat:'yy-mm-dd'})
            startDateField.val(format_date(calEvent.start));
            endRecPeriodField.datepicker({showOn:'both', buttonText:'choose', dateFormat:'yy-mm-dd'})
            endRecPeriodField.val(format_date(calEvent.end_recurring_period));
            startField.val(calEvent.start);
            endField.val(calEvent.end);
            setupStartAndEndTimeFields(startField, endField, calEvent, $calendar.weekCalendar("getTimeslotTimes", calEvent.start));
            $(window).resize().resize(); //fixes a bug in modal overlay size ??
        });
    }

    function editOccurrence(calEvent, $event) {
        /* TODO add an editable date field to dialog */
        var $dialogContent = $("#occurrence_edit_container");
        resetForm($dialogContent);
        var startField = $dialogContent.find("select[name='start']").val(calEvent.start);
        var endField =  $dialogContent.find("select[name='end']").val(calEvent.end);
        var titleField = $dialogContent.find("input[name='title']").val(calEvent.title);
        var bodyField = $dialogContent.find("textarea[name='body']").val(calEvent.body);

        $dialogContent.dialog({
            modal: true,
            title: "Edit - " + calEvent.title,
            close: function() {
                $dialogContent.dialog("destroy");
                $dialogContent.hide();
                $('#calendar').weekCalendar("removeUnsavedEvents");
            },
            buttons: {
            save : function(){
                /* send new data to the server; if response is OK
                * then update calendar and close dialog */
                start = new Date(startField.val());
                end = new Date(endField.val());
                title = titleField.val();
                body = bodyField.val();
                st = format_datetime(start);
                en = format_datetime(end);
                data = {id:calEvent.id, start:st, end:en, title:title, description:body};
                $.post(edit_occurrence_url, data, function(data){
                    if(data.error == undefined){
                        evt = data[0];
                        calEvent.id = evt['id'];
                        calEvent.start = start;
                        calEvent.end = end;
                        calEvent.title = title;
                        calEvent.body = body;
                        calEvent.recurring = evt.recurring;
                        calEvent.persisted = evt.persisted;
                        $calendar.weekCalendar("updateEvent", calEvent);
                        $dialogContent.dialog("close");
                    }else{
                        alert(data.error);
                    }
                }, 'json');
                },
                "delete" : function(){
                    data = {id:calEvent.id, action:"cancel"};
                    $.post(edit_occurrence_url, data, function(data){
                        if(data.error == undefined){
                            $calendar.weekCalendar("removeEvent", calEvent.id);
                            $dialogContent.dialog("close");
                        }else{
                            alert(data.error);
                        }
                    });
                },
                cancel : function(){
                    $dialogContent.dialog("close");
                }
            }
        }).show();

        startField = $dialogContent.find("select[name='start']").val(calEvent.start);
        endField =  $dialogContent.find("select[name='end']").val(calEvent.end);
        $dialogContent.find(".date_holder").text($calendar.weekCalendar("formatDate", calEvent.start));
        setupStartAndEndTimeFields(startField, endField, calEvent, $calendar.weekCalendar("getTimeslotTimes", calEvent.start));
        $(window).resize().resize(); //fixes a bug in modal overlay size ??
    }
    
    function resetForm($dialogContent) {
        $dialogContent.find("input").val("");
        $dialogContent.find("textarea").val("");
    }

    function getTestEventData() {
        var year = new Date().getFullYear();
        var month = new Date().getMonth();
        var day = new Date().getDate();

        return {
            events : [
            {"id":1, "start": new Date(year, month, day, 12), "end": new Date(year, month, day, 13, 30),"title":"Lunch with Mike"},
            {"id":2, "start": new Date(year, month, day, 14), "end": new Date(year, month, day, 14, 45),"title":"Dev Meeting"},
            {"id":3, "start": new Date(year, month, day + 1, 17), "end": new Date(year, month, day + 1, 17, 45),"title":"Hair cut"},
            {"id":4, "start": new Date(year, month, day - 1, 8), "end": new Date(year, month, day - 1, 9, 30),"title":"Team breakfast"},
            {"id":5, "start": new Date(year, month, day + 1, 14), "end": new Date(year, month, day + 1, 15),"title":"Product showcase"},
            {"id":6, "start": new Date(year, month, day, 10), "end": new Date(year, month, day, 11),"title":"I'm read-only", readOnly : true}

            ]
        };
    }


    /*
    * Sets up the start and end time fields in the calendar event
    * form for editing based on the calendar event being edited
    */
    function setupStartAndEndTimeFields($startTimeField, $endTimeField, calEvent, timeslotTimes) {
        // TODO optimize - we don't need to recreate options every time
        $startTimeField.empty();
        $endTimeField.empty();
        var event_start = calEvent.start.getTime();
        var event_end = calEvent.end.getTime();
        var have_start = false;
        var have_end = false;
        for(var i=0; i<timeslotTimes.length; i++) {
            var startTime = timeslotTimes[i].start;
            var endTime = timeslotTimes[i].end;
            var startSelected = "";
            if(!have_start){
                if(startTime.getTime() >= event_start) {
                    startSelected = "selected=\"selected\"";
                    have_start = true;
                }
            }
            var endSelected = "";
            if(!have_end){
                if(endTime.getTime() >= event_end) {
                    endSelected = "selected=\"selected\"";
                    have_end = true;
                }
            }
            $startTimeField.append("<option value=\"" + startTime + "\" " + startSelected + ">" + timeslotTimes[i].startFormatted + "</option>");
            $endTimeField.append("<option value=\"" + endTime + "\" " + endSelected + ">" + timeslotTimes[i].endFormatted + "</option>");
        }
        $endTimeOptions = $endTimeField.find("option");
        $startTimeField.trigger("change");
    }

    var $endTimeField = $("select[name='end']");
    var $endTimeOptions;// = $endTimeField.find("option");

    //reduces the end time options to be only after the start time options.
    $("select[name='start']").change(function(){
        var startTime = $(this).find(":selected").val();
        var currentEndTime = $endTimeField.val();
        $endTimeField.html(
            $endTimeOptions.filter(function(){
                return startTime < $(this).val();
            })
        );
        var endTimeSelected = false;
        // TODO this loop can probably be eliminated too
        $endTimeOptions.each(function() {
            if($(this).val() == currentEndTime) {
                $endTimeField.val(currentEndTime);
                endTimeSelected = true;
                return false;
            }
            return true;
        });

        if(!endTimeSelected) {
            //automatically select an end date 2 slots away.
            $endTimeField.find("option:eq(1)").attr("selected", "selected");
        }

    });


    var $about = $("#about");


    {% if periods.week.start %}
    /* jump to initial date */
    var year = {{periods.week.start.year}};
    var month = {{periods.week.start.month}} - 1; /* we count from 1 */
    var day = {{periods.week.start.day}};
    var initial_date = new Date(year, month, day);
    $calendar.weekCalendar("gotoWeek", initial_date);
    {% endif %}
});
