/*
 * A local settings file for weekcalendar.
 * I'm not sure if it is a good idea, but other options have obvious drawbacks:
 * - using main settings.py pollutes it with plenty of options for various UIs,
 *   and requires modifications to core engine which is not desirable
 * - putting config in weekcalendar.js or in calendar_week.html limits
 *   flexibility
 * For want of a better idea, here it is.
 **/
timeslotsPerHour = 4;
allowCalEventOverlap = true;
firstDayOfWeek = 1;
businessHours = {start: 8, end: 18, limitDisplay: true };