
function weekcal_save_event(calEvent){
    /* post data to the server
     * if the server returns an error we display alert
     * and reload page to get back to original values
     * */
    start = calEvent.start;
    end = calEvent.end;
    title = calEvent.title;
    body = calEvent.body;
    st = format_datetime(start);
    en = format_datetime(end);
    data = {id:calEvent.id, start:st, end:en, title:title, description:body};
    $.post(edit_occurrence_url, data, function(data){
        if(data=='OK'){
            // pass
        }else{
            alert(data);
            window.location.reload();
        }
    });
}


$(document).ready(function() {


    var $calendar = $('#calendar');
    var id = 10;

    $calendar.weekCalendar({
         /* TODO input parameters dynamically from settings */
        timeslotsPerHour : 4,
        allowCalEventOverlap : true,
        firstDayOfWeek : 1,
        businessHours :{start: 8, end: 18, limitDisplay: true },
        height : function($calendar) {
            return $(window).height() - $("h1").outerHeight();
        },
        eventRender : function(calEvent, $event) {
            if (calEvent.end.getTime() < new Date().getTime()) {
                /* past events grayed out */
                /* TODO this should be (a) optional, (b) styled by CSS file */
                $event.css("backgroundColor", "#aaa");
                $event.find(".time").css({
                            "backgroundColor" : "#999",
                            "border" : "1px solid #888"
                        });
            }
        },
        draggable : function(calEvent, $event) {
            return calEvent.readOnly != true;
        },
        resizable : function(calEvent, $event) {
            return calEvent.readOnly != true;
        },
        eventNew : function(calEvent, $event) {
            var $dialogContent = $("#event_edit_container");
            resetForm($dialogContent);
            var startField = $dialogContent.find("select[name='start']").val(calEvent.start);
            var endField =  $dialogContent.find("select[name='end']").val(calEvent.end);
            var titleField = $dialogContent.find("input[name='title']");
            var bodyField = $dialogContent.find("textarea[name='body']");
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
                        /* TODO save old params, send AJAX request to save new data, restore old data upon receiving
                        * error message from server */
                        calEvent.id = id;
                        id++;
                        calEvent.start = new Date(startField.val());
                        calEvent.end = new Date(endField.val());
                        calEvent.title = titleField.val();
                        calEvent.body = bodyField.val();

                        $calendar.weekCalendar("removeUnsavedEvents");
                        $calendar.weekCalendar("updateEvent", calEvent);
                        $dialogContent.dialog("close");
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
            weekcal_save_event(calEvent);
        },

        eventResize : function(calEvent, $event) {
            weekcal_save_event(calEvent);
        },

        eventClick : function(calEvent, $event) {
            if(calEvent.readOnly) {
                return;
            }

            /* TODO add an editable date field to dialog */
            var $dialogContent = $("#event_edit_container");
            resetForm($dialogContent);
            var startField = $dialogContent.find("select[name='start']").val(calEvent.start);
            var endField =  $dialogContent.find("select[name='end']").val(calEvent.end);
            var titleField = $dialogContent.find("input[name='title']").val(calEvent.title);
            var bodyField = $dialogContent.find("textarea[name='body']");
            bodyField.val(calEvent.body);

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
                        if(data=='OK'){
                            calEvent.start = start;
                            calEvent.end = end;
                            calEvent.title = title;
                            calEvent.body = body;
                            $dialogContent.dialog("close");
                            $calendar.weekCalendar("updateEvent", calEvent);
                        }else{
                            alert(data);
                        }
                    });

                    },
                    "delete" : function(){
                        $calendar.weekCalendar("removeEvent", calEvent.id);
                        $dialogContent.dialog("close");
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

        },

        eventMouseover : function(calEvent, $event) {
        },

        eventMouseout : function(calEvent, $event) {
        },

        noEvents : function() {
        },

        data : function(start, end, callback) {
            /* this is called (a) upon page load and (b) when week is changed
            * start and end are beginning/end of selected week */
            var base_url = '{% url week_calendar_json calendar_slug=calendar_slug %}';
            var url = base_url + '?year=' + start.getFullYear() + '&month=' + (start.getMonth() + 1) + '&day=' + start.getDate();
            $.getJSON(url, function(data){
                res = {events:data};
                callback(res);
            });
        }
    });

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

        for(var i=0; i<timeslotTimes.length; i++) {
            var startTime = timeslotTimes[i].start;
            var endTime = timeslotTimes[i].end;
            var startSelected = "";
            if(startTime.getTime() === calEvent.start.getTime()) {
                startSelected = "selected=\"selected\"";
            }
            var endSelected = "";
            if(endTime.getTime() === calEvent.end.getTime()) {
                endSelected = "selected=\"selected\"";
            }
            $startTimeField.append("<option value=\"" + startTime + "\" " + startSelected + ">" + timeslotTimes[i].startFormatted + "</option>");
            $endTimeField.append("<option value=\"" + endTime + "\" " + endSelected + ">" + timeslotTimes[i].endFormatted + "</option>");
        }
        $endTimeOptions = $endTimeField.find("option");
        $startTimeField.trigger("change");
    }

    var $endTimeField = $("select[name='end']");
    var $endTimeOptions = $endTimeField.find("option");

    //reduces the end time options to be only after the start time options.
    $("select[name='start']").change(function(){
        var startTime = $(this).find(":selected").val();
        var currentEndTime = $endTimeField.find("option:selected").val();
        $endTimeField.html(
            $endTimeOptions.filter(function(){
                return startTime < $(this).val();
            })
        );

        var endTimeSelected = false;
        $endTimeField.find("option").each(function() {
            if($(this).val() === currentEndTime) {
                $(this).attr("selected", "selected");
                endTimeSelected = true;
                return false;
            }
        });

        if(!endTimeSelected) {
            //automatically select an end date 2 slots away.
            $endTimeField.find("option:eq(1)").attr("selected", "selected");
        }

    });


    var $about = $("#about");


    {% if start_date %}
    /* jump to initial date */
    var year = {{start_date.year}};
    var month = {{start_date.month}} - 1; /* we count from 1 */
    var day = {{start_date.day}};
    var initial_date = new Date(year, month, day);
    $calendar.weekCalendar("gotoWeek", initial_date);
    {% endif %}
});
