
edit_occurrence_url = "{% url edit_occurrence_by_code %}"

function lead_zero(v){
    if(v<10){
        v = '0' + v;
    }
    return v;
}

function format_datetime(dt){
    var s = ''
    s = s + dt.getFullYear() + '-' + lead_zero(dt.getMonth()+1) + '-' + lead_zero(dt.getDate());
    s = s + ' '
    s = s + lead_zero(dt.getHours()) + ':' + lead_zero(dt.getMinutes()) + ':' + lead_zero(dt.getSeconds());
    return s
}
