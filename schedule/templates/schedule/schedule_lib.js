
function lead_zero(v){
    /* utility function for formatting datetime */
    if(v<10){
        v = '0' + v;
    }
    return v;
}

function format_datetime(dt){
    /* takes a Date object and returns formatted string which is accepted
     * by Django form
     **/
    var s = ''
    s = s + dt.getFullYear() + '-' + lead_zero(dt.getMonth()+1) + '-' + lead_zero(dt.getDate());
    s = s + ' '
    s = s + lead_zero(dt.getHours()) + ':' + lead_zero(dt.getMinutes()) + ':' + lead_zero(dt.getSeconds());
    return s
}

/* global var for use by ajax scripts */
edit_occurrence_url = "{% url ajax_edit_occurrence_by_code %}";
get_week_occurrences_url = '{% url week_calendar_json calendar_slug=calendar.slug %}';
edit_event_url = "{% url ajax_edit_event calendar_slug=calendar.slug %}";
user_is_authenticated = {{user.is_authenticated|yesno:"true,false"}};
username = "{{user.username}}";
get_event_url = "{% url event_json %}";