# Remove Bower & Modernize Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove deprecated django-bower dependency and modernize all frontend assets to Bootstrap 5, FullCalendar 6, and vanilla JS (no jQuery).

**Architecture:** Replace bower-managed static assets with CDN links. Rewrite all JavaScript to use vanilla JS and modern APIs (fetch, Bootstrap 5 JS, FullCalendar 6). Update all templates from Bootstrap 3 classes/attributes to Bootstrap 5 equivalents.

**Tech Stack:** Bootstrap 5.3 (CDN), Bootstrap Icons (CDN), FullCalendar 6 (CDN), vanilla JavaScript

---

### Task 1: Update `base.html` — CDN links and remove jQuery

**Files:**
- Modify: `schedule/templates/base.html`

**Step 1: Replace the file contents**

Replace the entire `<head>` section. Remove jQuery, jQuery UI, Bootstrap 3 static refs. Add Bootstrap 5 CSS+JS and Bootstrap Icons from CDN. Keep `schedule.js` and `schedule.css` static refs.

```html
{% load i18n static %}
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" dir="{% if LANGUAGE_BIDI %}rtl{% else %}ltr{% endif %}" xml:lang="{{ LANGUAGE_CODE }}" lang="{{ LANGUAGE_CODE }}">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>{% if site_name %}{{ site_name }} : {% endif %}{% block head_title %}{% endblock %}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" type="text/css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" type="text/css">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
        <script type="text/javascript" src="{% static "schedule.js" %}"></script>
        <link rel="stylesheet" href="{% static "schedule.css" %}" type="text/css" media="screen">
        {% block extra_head %}
        {% endblock %}
    </head>

    <body>
    <h3 id="demo">{% trans "This is a demo of a django-schedule calendar" %}</h3>
    <p style="clear:both">

        <div id="body">
            {% if messages %}
                <ul id="messages">
                    {% for message in messages %}
                    <li id="message_{{ forloop.counter }}"><a href="#" onclick="document.getElementById('message_{{ forloop.counter }}').style.display='none'; return false;"><small>{% trans "clear" %}</small></a> {{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}

            {% block body %}
            {% endblock %}

        </div>

        <div id="footer">{% block footer %}{% endblock %}</div>

    </body>
</html>
```

Key changes:
- Bootstrap 3 static → Bootstrap 5.3.3 CDN
- Added Bootstrap Icons CDN
- Removed jQuery (`jquery/dist/jquery.js`)
- Removed jQuery UI (`jquery-ui/jquery-ui.min.js`, `jquery-ui/themes/base/all.css`)
- Removed Bootstrap 3 JS (`bootstrap/dist/js/bootstrap.js`)
- Added `bootstrap.bundle.min.js` (includes Popper)
- Replaced `$('#message_...').fadeOut()` with vanilla `style.display='none'`

**Step 2: Commit**

```bash
git add schedule/templates/base.html
git commit -m "feat: update base.html to Bootstrap 5 CDN, remove jQuery"
```

---

### Task 2: Modernize `schedule.css`

**Files:**
- Modify: `schedule/static/schedule.css`

**Step 1: Replace with modern CSS**

Remove all IE6-9 filter hacks, vendor-prefix gradients. The `.gradient` class is removed entirely — Bootstrap 5's default `btn-primary` styling is sufficient.

```css
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  text-align: center;
}

a {
  color: #000;
}

table, th, td {
  border-left: 1px solid #dddddd;
}

.btn-primary a strong {
  color: #FFF;
}

.btn-custom {
  background-color: #e6e6e6;
  border: 1px solid #cccccc;
}
.btn-custom:hover,
.btn-custom:focus,
.btn-custom:active,
.btn-custom.active {
  background-color: #d9d9d9;
  border-color: #cdcdcd;
}

.row-centered {
    text-align: center;
}

.modal-content {
  color: #000;
}

.center {
     float: none;
     margin-left: auto;
     margin-right: auto;
}
```

**Step 2: Commit**

```bash
git add schedule/static/schedule.css
git commit -m "feat: remove IE vendor-prefix CSS hacks, drop gradient class"
```

---

### Task 3: Rewrite `schedule.js` — jQuery UI dialogs to Bootstrap 5 modals

**Files:**
- Modify: `schedule/static/schedule.js`

**Step 1: Replace with vanilla JS using Bootstrap 5 modal API**

The old code used jQuery UI `.dialog()`. The new code uses Bootstrap 5 `Modal` class. The `_dialogs.html` template will be updated in the next task to match.

```javascript
function openCancelDialog(node, cancel_url, delete_url, event) {
  event.stopPropagation();
  var modalEl = document.getElementById('delete_dialog');
  var thisBtn = modalEl.querySelector('.btn-this');
  var allBtn = modalEl.querySelector('.btn-all');
  thisBtn.onclick = function() { window.location = cancel_url; };
  allBtn.onclick = function() { window.location = delete_url; };
  var modal = new bootstrap.Modal(modalEl);
  modal.show();
  return false;
}

function openEditDialog(node, occurrence_url, event_url, event) {
  event.stopPropagation();
  var modalEl = document.getElementById('edit_dialog');
  var thisBtn = modalEl.querySelector('.btn-this');
  var allBtn = modalEl.querySelector('.btn-all');
  thisBtn.onclick = function() { window.location = occurrence_url; };
  allBtn.onclick = function() { window.location = event_url; };
  var modal = new bootstrap.Modal(modalEl);
  modal.show();
  return false;
}

function openDetail(node) {
  var targetId = node.getAttribute('href');
  var modalEl = document.querySelector(targetId);
  var modal = new bootstrap.Modal(modalEl);
  modal.show();
  return false;
}

function openURL(url, event) {
    event.stopPropagation();
    window.location = url;
}
```

**Step 2: Commit**

```bash
git add schedule/static/schedule.js
git commit -m "feat: rewrite schedule.js from jQuery UI to Bootstrap 5 modals"
```

---

### Task 4: Rewrite `_dialogs.html` — jQuery UI to Bootstrap 5 modals

**Files:**
- Modify: `schedule/templates/schedule/_dialogs.html`

**Step 1: Replace jQuery UI hidden divs with Bootstrap 5 modal markup**

The old code used hidden `<div>` elements that jQuery UI turned into dialogs. The new code uses proper Bootstrap 5 modal structure with `.btn-this` and `.btn-all` classes that `schedule.js` hooks into.

```html
{% load i18n %}

<div class="modal fade" id="delete_dialog" tabindex="-1" aria-labelledby="deleteDialogLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="deleteDialogLabel">{% trans "Question" %}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{% trans 'Close' %}"></button>
      </div>
      <div class="modal-body">
        {% trans "Do you want to cancel this occurrence or delete all occurrences of this event?" %}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-this">{% trans "This" %}</button>
        <button type="button" class="btn btn-danger btn-all">{% trans "All" %}</button>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{% trans "Do nothing" %}</button>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="edit_dialog" tabindex="-1" aria-labelledby="editDialogLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="editDialogLabel">{% trans "This is a recurring event" %}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{% trans 'Close' %}"></button>
      </div>
      <div class="modal-body">
        {% trans "Do you want to edit this occurrence or all occurrences?" %}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary btn-this">{% trans "This" %}</button>
        <button type="button" class="btn btn-primary btn-all">{% trans "All" %}</button>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{% trans "Do nothing" %}</button>
      </div>
    </div>
  </div>
</div>
```

**Step 2: Commit**

```bash
git add schedule/templates/schedule/_dialogs.html
git commit -m "feat: convert _dialogs.html from jQuery UI to Bootstrap 5 modals"
```

---

### Task 5: Update Bootstrap classes in simple templates (batch)

**Files:**
- Modify: `schedule/templates/schedule/_create_event_options.html`
- Modify: `schedule/templates/schedule/_next.html`
- Modify: `schedule/templates/schedule/_prev.html`
- Modify: `schedule/templates/schedule/_event_options.html`
- Modify: `schedule/templates/schedule/event.html`
- Modify: `schedule/templates/schedule/occurrence.html`
- Modify: `schedule/templates/schedule/_day_cell.html`
- Modify: `schedule/templates/schedule/calendar_day.html`

**Step 1: Update `_create_event_options.html`**

Change `glyphicon glyphicon-plus` → `bi bi-plus`:

```html
<a href="{{ create_event_url }}&amp;next={{here}}">
  <span class="bi bi-plus"></span>
</a>
```

**Step 2: Update `_next.html`**

Change `glyphicon glyphicon-circle-arrow-right` → `bi bi-arrow-right-circle`:

```html
<a href="{{ url|safe }}"><span class="bi bi-arrow-right-circle"></span></a>
```

**Step 3: Update `_prev.html`**

Change `glyphicon glyphicon-circle-arrow-left` → `bi bi-arrow-left-circle`:

```html
<a href="{{ url|safe }}"><span class="bi bi-arrow-left-circle"></span></a>
```

**Step 4: Update `_event_options.html`**

Replace all `glyphicon glyphicon-pencil` → `bi bi-pencil` and `glyphicon glyphicon-remove` → `bi bi-x-circle`:

```html
<span class="actions">
{% if edit_event %}
  <span class="edit">
  {% if occurrence.event.rule %}
    {% if occurrence.id %}
        <a href="#" onclick="openURL('{{ edit_occurrence }}?next={{ here }}', event);">
          <span class="bi bi-pencil"></span>
        </a>
    {% else %}
        <a href="#" onclick="openEditDialog(this, '{{ edit_occurrence }}?next={{ here }}', '{{ edit_event }}?next={{ here }}', event);">
          <span class="bi bi-pencil"></span>
        </a>
    {% endif %}
  {% else %}
    <a href="#" onclick="openURL('{{ edit_event }}?next={{ here }}', event);">
        <span class="bi bi-pencil"></span>
    </a>
  {% endif %}
  </span>
{% endif %}

{% if delete_event %}
<span class="delete">
  {% if occurrence.event.rule %}
    {% if occurrence.id %}
        <a href="#" onclick="openURL('{{cancel_occurrence}}?next={{here}}', event);">
          <span class="bi bi-x-circle"></span>
        </a>
    {% else %}
        <a href="#" onclick="openCancelDialog(this, '{{ cancel_occurrence }}?next={{here}}', '{{delete_event}}?next={{here}}', event);">
          <span class="bi bi-x-circle"></span>
        </a>
    {% endif %}
  {% else %}
    <a href="#" onclick="openURL('{{delete_event}}?next={{here}}', event);">
      <span class="bi bi-x-circle"></span>
    </a>
  {% endif %}
</span>
{% endif %}
</span>
```

**Step 5: Update `event.html`**

Replace `btn-primary gradient` → `btn-primary`, glyphicons → Bootstrap Icons:

```html
{% extends "base.html" %}
{% load i18n scheduletags %}

{% block body %}
<div class="navigation">
  <a class="btn btn-primary" href="{% url "day_calendar" event.calendar.slug %}{% querystring_for_date event.start 3 %}">
    {% trans "Day" %}
  </a>
  <a class="btn btn-primary" href="{% url "month_calendar" event.calendar.slug %}{% querystring_for_date event.start 2 %}">
    {% trans "Month" %}
  </a>
  <a class="btn btn-primary" href="{% url "year_calendar" event.calendar.slug %}{% querystring_for_date event.start 1 %}">
    {% trans "Year" %}
  </a>
</div>

<div class="event_actions" align="center">
  {% if back_url %}
  <a href="{{ back_url }}">
    <span class="bi bi-arrow-left-circle"></span>
  </a>
  &nbsp;
  {% endif %}
  <a href="{% url "edit_event" event.calendar.slug event.id %}">
   {% trans "Edit" %} <span class="bi bi-pencil"></span>
  </a>
  &nbsp;
  <a href="{% url "delete_event" event.id %}">
   {% trans "Delete" %} <span class="bi bi-x-circle"></span>
  </a>
</div>
<h2 align="center">{{event.title}}</h2>
<table align="center" class="table table-hover">
<tr>
<td>{% trans "Starts" %}</td>
<td>{% blocktrans with event.start|date:_("DATETIME_FORMAT") as start_date %}{{ start_date }}{% endblocktrans %}</td>
</tr>
<tr>
<td>{% trans "Ends" %}</td>
<td>{% blocktrans with event.end|date:_("DATETIME_FORMAT") as end_date %}{{ end_date }}{% endblocktrans %}</td>
</tr>
<tr>
<td>{% trans "Reoccurs" %}</td>
{% if event.rule %}
<td>{{ event.rule.name }} {% trans "until" %} {% blocktrans with event.end_recurring_period|date:_("DATETIME_FORMAT") as end_recurring_date %}{{ end_recurring_date }}{% endblocktrans %}</td>
{% else %}
<td>{% trans "Never. This is a 'one time only' event." %}</td>
{% endif %}
</tr></table>
{% if event.description %}
<h3>{% trans "Description" %}</h3>
<p>{{event.description}}</p>
{% endif %}

{% endblock %}
```

**Step 6: Update `occurrence.html`**

Same pattern as `event.html`:

```html
{% extends "base.html" %}
{% load i18n scheduletags %}

{% block body %}
<div class="navigation">
  <a class="btn btn-primary" href="{% url "day_calendar" occurrence.event.calendar.slug %}{% querystring_for_date occurrence.start 3 %}">
    {% trans "Day" %}
  </a>
  <a class="btn btn-primary" href="{% url "month_calendar" occurrence.event.calendar.slug %}{% querystring_for_date occurrence.start 2 %}">
    {% trans "Month" %}
  </a>
  <a class="btn btn-primary" href="{% url "year_calendar" occurrence.event.calendar.slug %}{% querystring_for_date occurrence.start 1 %}">
    {% trans "Year" %}
  </a>
</div>

<div class="event_actions" align="center">
  {% if back_url %}
  <a href="{{ back_url }}">
    <span class="bi bi-arrow-left-circle"></span>
  </a>
  &nbsp;
  {% endif %}
  <a href="{{occurrence.get_edit_url}}">
   {% trans "Edit" %} <span class="bi bi-pencil"></span>
  </a>
  &nbsp;
  <a href="{{occurrence.get_cancel_url}}">
   {% trans "Delete" %} <span class="bi bi-x-circle"></span>
  </a>
</div>
<h2 align="center">{{occurrence.title}}</h2>
<table align="center" class="table table-hover">
<tr>
<td>{% trans "Starts" %}</td>
<td>{% blocktrans with occurrence.start|date:_("DATETIME_FORMAT") as start_date %}{{ start_date }}{% endblocktrans %}</td>
</tr>
<tr>
<td>{% trans "Ends" %}</td>
<td>{% blocktrans with occurrence.end|date:_("DATETIME_FORMAT") as end_date %}{{ end_date }}{% endblocktrans %}</td>
</tr>
<tr>
<td>{% trans "Reoccurs" %}</td>
{% if occurrence.event.rule %}
<td>{{ occurrence.event.rule.name }} {% trans "until" %} {% blocktrans with occurrence.event.end_recurring_period|date:_("DATETIME_FORMAT") as end_recurring_date %}{{ end_recurring_date }}{% endblocktrans %}</td>
{% else %}
<td>{% trans "Never. This is a 'one time only' event." %}</td>
{% endif %}
</tr></table>
{% if occurrence.description %}
<h3>{% trans "Description" %}</h3>
<p>{{occurrence.description}}</p>
{% endif %}

{% endblock %}
```

**Step 7: Update `_day_cell.html`**

Replace `btn-primary gradient` → `bg-primary text-white`:

```html
{% load scheduletags %}
{% if day.start.month != month.start.month %}
  <td class="muted"></td>
{% else %}
  {% if day.has_occurrences %}
    <td class="bg-primary text-white">
  {% else %}
    <td>
  {% endif %}
  <a href="{% url "day_calendar" calendar.slug %}{% querystring_for_date day.start 3 %}">
    <strong>{{day.start.day}}</strong>
  </a>
  {% if size != "small" %}
    {% include "schedule/_day_cell_big.html" %}
  {% endif %}
</td>
{% endif %}
```

**Step 8: Update `calendar_day.html`**

Replace `btn-primary gradient` → `btn-primary`:

```html
{% extends "base.html" %}
{% load scheduletags i18n %}

{% block body %}

{% include "schedule/_dialogs.html" %}
<div class="row row-centered">
  <a class="btn btn-primary" href="{% url "week_calendar" calendar.slug %}{% querystring_for_date period.start 3 %}">
    {% trans "Week" %}
  </a>
  <a class="btn btn-primary" href="{% url "month_calendar" calendar.slug %}{% querystring_for_date period.start 2 %}">
    {% trans "Month" %}
  </a>
  <a class="btn btn-primary" href="{% url "year_calendar" calendar.slug %}{% querystring_for_date period.start 1 %}">
    {% trans "Year" %}
  </a>
</div>
<div class="row row-centered">
    <h1>{{ calendar.name }}</h1>
    {% prevnext "day_calendar" calendar period "l, F d, Y" %}
    <div class="now">
      <a class="btn btn-primary" href="{% url "day_calendar" calendar.slug %}">
        {% trans "Today" %}
      </a>
    </div>
</div>
  <div class="row row-centered">
    <div>
      {% daily_table period %}
    </div>
</div>

{% endblock %}
```

**Step 9: Commit**

```bash
git add schedule/templates/schedule/_create_event_options.html schedule/templates/schedule/_next.html schedule/templates/schedule/_prev.html schedule/templates/schedule/_event_options.html schedule/templates/schedule/event.html schedule/templates/schedule/occurrence.html schedule/templates/schedule/_day_cell.html schedule/templates/schedule/calendar_day.html
git commit -m "feat: update Bootstrap 3 classes to Bootstrap 5 across templates"
```

---

### Task 6: Update modal templates for Bootstrap 5

**Files:**
- Modify: `schedule/templates/schedule/_detail.html`
- Modify: `schedule/templates/schedule/_daily_table.html`
- Modify: `schedule/templates/schedule/_day_cell_big.html`
- Modify: `schedule/templates/fullcalendar_modal.html`
- Modify: `schedule/templates/fullcalendar.html`

**Step 1: Update `_detail.html`**

Replace `data-dismiss` → `data-bs-dismiss`, `btn-default` → `btn-secondary`, close button to Bootstrap 5 style:

```html
{% load i18n %}
{% load scheduletags %}

<div class="modal fade" id="{% hash_occurrence occurrence %}" tabindex="-1" role="dialog" >
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">{{occurrence.title}}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{% trans 'Close' %}"></button>
      </div>
      <div class="modal-body">
        <table class="table table-striped">
            <tr>
                <td class="left">{% trans "Starts" %}</td>
                <td>{% blocktrans with occurrence.start|date:_("DATETIME_FORMAT") as start_date %}{{ start_date }}{% endblocktrans %}</td>
            </tr>
            <tr>
                <td class="left">{% trans "Ends" %}</td>
                <td>{% blocktrans with occurrence.end|date:_("DATETIME_FORMAT") as end_date %}{{ end_date }}{% endblocktrans %}</td>
            </tr>
            {% if occurrence.event.rule %}
                {% if not occurrence.id %}
                    <tr>
                        <td class="left">{% trans "Reoccurs" %}</td><td>{{occurrence.event.rule}}</td>
                    </tr>
                    {% if occurrence.event.end_recurring_period %}
                        <tr>
                            <td class="left">{% trans "Until" %}</td>
                            <td>{% blocktrans with occurrence.event.end_recurring_period|date:_("DATETIME_FORMAT") as end_date %}{{ end_date }}{% endblocktrans %}</td>
                        </tr>
                    {% endif %}
                {% endif %}
            {% endif %}
        </table>
        {% if occurrence.description %}
        <h3>{% trans "Description" %}</h3>
        <p>{{occurrence.description}}</p>
        {% endif %}
      </div>
      <div class="modal-footer">
       <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{% trans "Close" %}</button>
      </div>
    </div>
  </div>
</div>
```

**Step 2: Update `_daily_table.html`**

Replace `data-toggle` → `data-bs-toggle`, `data-target` → `data-bs-target`:

```html
{% load scheduletags %}
<table class="table table-striped">
    {% for slot in slots %}
    <tr>
    <td class="col-md-1">
      <span class="time">{{ slot.start|time:"G:i" }}</span>
      {% if addable %}
      {% create_event_url calendar slot.start %}
      {% endif %}
    </td>
    <td class="col-md-4">
      {% for occ in slot.occurrences %}
      <button type="button"  class="btn {% if occ.cancelled %} btn-danger {%else%} btn-primary {% endif %}" data-bs-toggle="modal" data-bs-target="#{% hash_occurrence occ %}" {% if occ.event.color_event %} style="background-color: {{occ.event.color_event}};border-color:{{occ.event.color_event}}" {% endif %}>
                  {% options occ %}
                  {% title occ %}
            </button>
      {% include 'schedule/_detail.html' with occurrence=occ %}
      {% endfor %}
    </td>
  </tr>
    {% endfor %}
</table>
```

**Step 3: Update `_day_cell_big.html`**

Replace `data-toggle` → `data-bs-toggle`, `data-target` → `data-bs-target`, `data-dismiss` → `data-bs-dismiss`, `btn-default` → `btn-secondary`, close button:

```html
{% load scheduletags %}
<div>
  {% if day.has_occurrences %}
      {% for o in day.get_occurrence_partials %}
              <button type="button" class="btn btn-primary btn-lg" data-bs-toggle="modal" data-bs-target="#occurrenceModal">

                  <div class="starttime">
                      {% if o.class == 0 %}{{ o.occurrence.start|time:"G:i" }}{% endif %}
                      {% if o.class == 1 %}{{ o.occurrence.start|time:"G:i" }}{% endif %}
                      {% if o.class == 2 %}(All day){% endif %}
                      {% if o.class == 3 %}Ends at {{ o.occurrence.end|time:"G:i" }}{% endif %}
                  </div>
                  <div class="eventdesc">
                      {% title o.occurrence %}
                  </div>
              </div>
              <div class="modal fade" id="occurrenceModal" tabindex="-1" role="dialog" aria-labelledby="occurrence_detailsl">
                <div class="modal-dialog" role="document">
                  <div class="modal-content">
                    <div class="modal-header">
                      <h5 class="modal-title" id="myModalLabel">{{ occurrence.title }}</h5>
                      <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                      {% include 'schedule/_detail.html' with occurrence=o.occurrence %}
                    </div>
                   <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                  </div>
                </div>
              </div>
      {% endfor %}
  {% endif %}
</div>
```

**Step 4: Update `fullcalendar_modal.html`**

Replace `data-dismiss` → `data-bs-dismiss`, `btn-default` → `btn-secondary`, close button:

```html
{% load i18n %}
<div id="eventModal" class="modal fade" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog">

    <!-- Modal content-->
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title"><span id="EditorDelete"></span> {% trans "Event" %}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="{% trans 'Close' %}"></button>
      </div>
      <div class="modal-body">
       <p>{% blocktrans %}Would you like to <span id="editordelete"></span> all occurrences in this event or just this occurrence?{% endblocktrans %}</p>
      </div>
      <div class="modal-footer">
        <a href='#' id='allevent'>
         <button type="button" class="btn btn-secondary">{% trans "All" %}</button>
        </a>

        <a href='#' id='thisevent'>
         <button type="button" class="btn btn-secondary">{% trans "This" %}</button>
        </a>

        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{% trans "Close" %}</button>
      </div>
    </div>

  </div>
</div>
```

**Step 5: Update `fullcalendar.html`**

Replace `btn-primary gradient` → `btn-primary`, `glyphicon glyphicon-plus` → `bi bi-plus`:

```html
{% extends 'base.html' %}
{% load i18n %}

{% block head_title %}Calendar: {{ object.name }}{% endblock %}
{% block tab_id %}id='home_tab'{% endblock %}
{% block extra_head %}
    {% include "fullcalendar_script.html" %}
{% endblock %}

{% block body %}
    <a class="btn btn-primary" href="{% url 'calendar_create_event' calendar_slug %}">
        <span class='bi bi-plus'></span>
        {% trans "Add New Session" %}
    </a>
    <br>
    <br>
    <div id='calendar'></div>

    {% include "fullcalendar_modal.html" %}
{% endblock %}
```

**Step 6: Commit**

```bash
git add schedule/templates/schedule/_detail.html schedule/templates/schedule/_daily_table.html schedule/templates/schedule/_day_cell_big.html schedule/templates/fullcalendar_modal.html schedule/templates/fullcalendar.html
git commit -m "feat: update modal templates to Bootstrap 5 data attributes"
```

---

### Task 7: Rewrite `fullcalendar_script.html` — FullCalendar v6 + vanilla JS

**Files:**
- Modify: `schedule/templates/fullcalendar_script.html`

**Step 1: Complete rewrite**

Replace FullCalendar v2 + jQuery with FullCalendar v6 + vanilla JS + fetch API.

```html
{% load i18n %}

<link rel='stylesheet' type='text/css' href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.15/index.global.min.css' />
<script type='text/javascript' src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.15/index.global.min.js'></script>
<script type='text/javascript'>
document.addEventListener('DOMContentLoaded', function() {

    function getEventViewURL(event) {
        if (event.extendedProps.existed) {
            if ("{{ request.get_full_path }}".indexOf("/admin") != 0) {
                return "{% url 'occurrence' 12345 6789 %}".replace(/12345/, event.extendedProps.event_id).replace(/6789/, event.id);
            } else {
                return "{% url 'admin:schedule_occurrence_change' 12345 %}".replace(/12345/, event.id);
            }
        } else {
            if ("{{ request.get_full_path }}".indexOf("/admin") != 0) {
                return "{% url 'event' 12345 %}".replace(/12345/, event.extendedProps.event_id);
            } else {
                return "{% url 'admin:schedule_event_change' 12345 %}".replace(/12345/, event.extendedProps.event_id);
            }
        }
    }

    function setModalProperties(type, event) {
        var props = event.extendedProps;
        if (type == 'edit') {
            var tYPE = '{% trans "Edit" %}';
            var all_url = "{% url 'edit_event' calendar_slug 12345 %}".replace(/12345/, props.event_id);
            if (props.existed) {
                var this_url = "{% url 'edit_occurrence' 12345 6789 %}".replace(/12345/, props.event_id).replace(/6789/, event.id);
            } else {
                var this_url = "{% url 'edit_occurrence_by_date' 123 234 345 456 567 678 789 %}".replace(
                        /123/, props.event_id).replace(
                        /234/, props.year).replace(
                        /345/, props.month).replace(
                        /456/, props.day).replace(
                        /567/, props.hour).replace(
                        /678/, props.minute).replace(
                        /789/, props.second);
            }
        } else if (type == 'delete') {
            var tYPE = '{% trans "Delete" %}';
            var all_url = "{% url 'delete_event' 12345 %}".replace(/12345/, props.event_id);
            if (props.existed) {
                var this_url = "{% url 'cancel_occurrence' 12345 6789 %}".replace(/12345/, props.event_id).replace(/6789/, event.id);
            } else {
                var this_url = "{% url 'cancel_occurrence_by_date' 123 234 345 456 567 678 789 %}".replace(
                        /123/, props.event_id).replace(
                        /234/, props.year).replace(
                        /345/, props.month).replace(
                        /456/, props.day).replace(
                        /567/, props.hour).replace(
                        /678/, props.minute).replace(
                        /789/, props.second);
            }
        }

        document.getElementById('allevent').setAttribute('href', all_url);
        document.getElementById('thisevent').setAttribute('href', this_url);
        document.getElementById('editordelete').innerHTML = type;
        document.getElementById('EditorDelete').innerHTML = tYPE;
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        editable: true,
        dayMaxEvents: true,
        selectable: true,
        selectMirror: true,
        events: "{% url 'api_occurrences' %}?calendar_slug={{calendar_slug}}",
        loading: function(isLoading) {
            var el = document.getElementById('loading');
            if (el) {
                el.style.display = isLoading ? '' : 'none';
            }
        },
        eventDidMount: function(info) {
            var event = info.event;
            var element = info.el;
            var isTimeGrid = info.view.type.indexOf('timeGrid') === 0;

            if (isTimeGrid) {
                var titleEl = element.querySelector('.fc-event-title');
                if (titleEl) {
                    var link = document.createElement('a');
                    link.href = getEventViewURL(event);
                    link.innerHTML = titleEl.innerHTML;
                    titleEl.innerHTML = '';
                    titleEl.appendChild(link);
                }

                if (event.extendedProps.editable && "{{ request.get_full_path }}".indexOf("/admin") != 0) {
                    var timeEl = element.querySelector('.fc-event-time');
                    if (timeEl) {
                        var edit_button = document.createElement("button");
                        var edit_icon = document.createElement("span");
                        edit_button.className = 'btn btn-secondary btn-sm float-end edit_event';
                        edit_button.onclick = function(jsEvent) {
                            jsEvent.preventDefault();
                            jsEvent.stopPropagation();
                            setModalProperties('edit', event);
                            var modalEl = document.getElementById('eventModal');
                            var modal = new bootstrap.Modal(modalEl);
                            modal.show();
                        };
                        edit_icon.className = 'bi bi-pencil';
                        edit_button.appendChild(edit_icon);

                        var delete_button = document.createElement("button");
                        var delete_icon = document.createElement("span");
                        delete_button.className = 'btn btn-secondary btn-sm float-end delete_event';
                        delete_button.onclick = function(jsEvent) {
                            jsEvent.preventDefault();
                            jsEvent.stopPropagation();
                            setModalProperties('delete', event);
                            var modalEl = document.getElementById('eventModal');
                            var modal = new bootstrap.Modal(modalEl);
                            modal.show();
                        };
                        delete_icon.className = 'bi bi-trash';
                        delete_button.appendChild(delete_icon);

                        timeEl.insertAdjacentHTML('beforeend', '<br>');
                        timeEl.appendChild(edit_button);
                        timeEl.appendChild(delete_button);
                    }
                }
            }
        },
        dateClick: function(info) {
            if (info.view.type === 'dayGridMonth') {
                calendar.changeView('timeGridWeek', info.date);
            }
        },
        eventDrop: function(info) {
            var event = info.event;
            var delta = Math.round((event.start - info.oldEvent.start) / 60000);
            fetch("{% url 'api_move_or_resize' %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: new URLSearchParams({
                    'id': event.id,
                    'event_id': event.extendedProps.event_id,
                    'existed': event.extendedProps.existed,
                    'delta': delta
                })
            }).then(function(response) {
                return response.json();
            }).then(function(result) {
                calendar.refetchEvents();
            }).catch(function(error) {
                console.log(error);
                info.revert();
            });
        },
        eventResize: function(info) {
            var event = info.event;
            var delta = Math.round((event.end - info.oldEvent.end) / 60000);
            fetch("{% url 'api_move_or_resize' %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: new URLSearchParams({
                    'id': event.id,
                    'event_id': event.extendedProps.event_id,
                    'existed': event.extendedProps.existed,
                    'delta': delta,
                    'resize': true
                })
            }).then(function(response) {
                return response.json();
            }).then(function(result) {
                calendar.refetchEvents();
            }).catch(function(error) {
                console.log(error);
                info.revert();
            });
        },
        select: function(info) {
            fetch("{% url 'api_select_create' %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: new URLSearchParams({
                    'start': info.startStr,
                    'end': info.endStr,
                    'calendar_slug': '{{calendar_slug}}'
                })
            }).then(function(response) {
                return response.json();
            }).then(function(result) {
                calendar.refetchEvents();
            }).catch(function(error) {
                console.log(error);
            });
            calendar.unselect();
        }
    });
    calendar.render();
});
</script>
```

Key changes:
- Removed FullCalendar v2 CSS/JS CDN, moment.js, bootstrap-datetimepicker
- Added FullCalendar v6 CSS/JS CDN
- `$(document).ready()` → `document.addEventListener('DOMContentLoaded')`
- `$('#calendar').fullCalendar({...})` → `new FullCalendar.Calendar(calendarEl, {...})` + `calendar.render()`
- `header:` → `headerToolbar:`
- `month,agendaWeek,agendaDay` → `dayGridMonth,timeGridWeek,timeGridDay`
- `eventRender` → `eventDidMount` (FullCalendar v6 API)
- Event custom props now under `event.extendedProps`
- `$.ajax()` → `fetch()` with `URLSearchParams`
- `jQuery.trim()` → `.trim()`
- `dayClick` → `dateClick`
- `$('#calendar').fullCalendar('refetchEvents')` → `calendar.refetchEvents()`
- Bootstrap 5 modal API instead of jQuery `data-toggle`

**Step 2: Commit**

```bash
git add schedule/templates/fullcalendar_script.html
git commit -m "feat: rewrite fullcalendar_script.html for FullCalendar v6 + vanilla JS"
```

---

### Task 8: Update README — remove bower instructions

**Files:**
- Modify: `README.md`

**Step 1: Replace the "Static assets" section**

Remove the entire bower/django-bower section (lines 41-92) and replace with:

```markdown
Static assets
=============

Django Scheduler's bundled templates use [Bootstrap 5](https://getbootstrap.com/)
and [Bootstrap Icons](https://icons.getbootstrap.com/) loaded via CDN.
The FullCalendar view also loads [FullCalendar 6](https://fullcalendar.io/) via CDN.

No additional installation is needed — the default templates include all required
CSS and JavaScript from CDN links.

If you prefer to manage frontend assets yourself (e.g., via npm, or self-hosted files),
you can [override the templates](https://docs.djangoproject.com/en/stable/howto/overriding-templates/)
in your project.

Remember to execute "python manage.py collectstatic"
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: replace bower instructions with CDN-based approach in README"
```

---

### Task 9: Run tests and verify

**Step 1: Run the full test suite**

```bash
uv run pytest
```

Expected: All 149 tests pass. Template changes are frontend-only and should not affect any Python tests.

**Step 2: Run linters**

```bash
uv run black --check .
uv run ruff check .
```

Expected: No issues (only HTML/CSS/JS files were changed, which these linters don't check).
