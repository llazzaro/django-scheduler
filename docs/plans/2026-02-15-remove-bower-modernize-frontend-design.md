# Remove Bower and Modernize Frontend Assets

**Date:** 2026-02-15
**Status:** Approved

## Problem

The project's README recommends django-bower (deprecated) to install jQuery, jQuery UI, and Bootstrap 3 as static assets. The bundled templates use outdated libraries: Bootstrap 3, FullCalendar v2.3.1, jQuery, jQuery UI, and moment.js. A broken HTTP link to bootstrap-datetimepicker is also present.

## Approach: CDN-Based Modernization

Replace all bower/old static references with modern CDN links. No build tooling required.

- Bootstrap 3 -> Bootstrap 5.3 (CDN)
- FullCalendar v2 -> FullCalendar v6 (CDN)
- Drop jQuery and jQuery UI entirely
- Add Bootstrap Icons via CDN (replaces glyphicons)

## Changes

### 1. Templates: Bootstrap 3 to Bootstrap 5

Update all 12 affected template files:

- Replace Bootstrap 3 CDN/static refs with Bootstrap 5.3 CDN
- Replace `glyphicon` icons with Bootstrap Icons (`bi bi-*`)
- Update data attributes: `data-dismiss` -> `data-bs-dismiss`, `data-toggle` -> `data-bs-toggle`, `data-target` -> `data-bs-target`
- Replace `btn-default` -> `btn-secondary`, `pull-right` -> `float-end`
- Drop the `gradient` custom class and IE-era vendor-prefix CSS

Affected files:
- `schedule/templates/base.html`
- `schedule/templates/fullcalendar.html`
- `schedule/templates/fullcalendar_modal.html`
- `schedule/templates/fullcalendar_script.html`
- `schedule/templates/schedule/_create_event_options.html`
- `schedule/templates/schedule/_daily_table.html`
- `schedule/templates/schedule/_day_cell_big.html`
- `schedule/templates/schedule/_detail.html`
- `schedule/templates/schedule/_event_options.html`
- `schedule/templates/schedule/_next.html`
- `schedule/templates/schedule/_prev.html`
- `schedule/templates/schedule/event.html`
- `schedule/templates/schedule/occurrence.html`

### 2. Templates: FullCalendar v2 to v6

Rewrite `fullcalendar_script.html`:

- Replace FullCalendar v2 + moment.js CDN links with FullCalendar v6 CDN
- Use `new FullCalendar.Calendar(el, options)` instead of `$('#calendar').fullCalendar()`
- Replace `$.ajax()` with `fetch()` API
- Replace `$.ajaxSetup` CSRF handling with a helper using `fetch` headers
- Remove broken bootstrap-datetimepicker link

### 3. `schedule.js`: Drop jQuery UI

- Replace `$.dialog()` calls with Bootstrap 5 modal API (vanilla JS)
- Rewrite `openCancelDialog`, `openEditDialog`, `openDetail` to use native DOM

### 4. `schedule.css`: Clean up

- Remove IE6-9 filter hacks and vendor-prefix gradients
- Simplify to modern CSS

### 5. `base.html`: Update asset loading

- Replace bower static paths with Bootstrap 5 + Bootstrap Icons CDN
- Remove jQuery and jQuery UI script tags
- Keep `schedule.js` and `schedule.css` static references

### 6. README: Replace bower instructions

- Remove entire bower/django-bower section
- Document CDN-based approach for Bootstrap 5 and FullCalendar 6
- Note template override capability

### 7. Testing

- Run existing test suite (`uv run pytest`) to verify no Python-side breakage
- Frontend changes are template-only; no Python code affected
