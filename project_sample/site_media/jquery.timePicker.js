/*
 * Copyright (c) 2006 Sam Collett (http://www.texotela.co.uk)
 * Licensed under the MIT License:
 * http://www.opensource.org/licenses/mit-license.php
 */
 
/*
 * A time picker for jQuery
 * Based on original timePicker by Sam Collet (http://www.texotela.co.uk)
 * @name     timePicker
 * @version  0.1 
 * @author   Anders Fajerson (http://perifer.se)
 * @example  $("#mytime").timePicker();
 * @example  $("#mytime").timePicker({step:30, startTime:"15:00", endTime:"18:00"}); 
 */

(function($){
  
  $.fn.timePicker = function(options) {
    // Build main options before element iteration
	  var settings = $.extend({}, $.fn.timePicker.defaults, options);  
    
    return this.each(function() {
      $.timePicker(this, settings);
    });
  };
  
  $.timePicker = function (elm, settings) {
    var elm = $(elm)[0];  
    return elm.timePicker || (elm.timePicker = new jQuery._timePicker(elm, settings));
  };
  
  $._timePicker = function(elm, settings) {
    
    var tpOver = false;
    var startTime = normaliseTime(settings.startTime);
    var endTime = normaliseTime(settings.endTime);
    
    $(elm).attr('autocomplete', 'OFF'); // Disable browser autocomplete
    
    var times = [];
    var time = new Date(startTime); // Create a new date object.
    while(time <= endTime) {
      times[times.length] = formatTime(time, settings);
      time = new Date(time.setMinutes(time.getMinutes() + settings.step));
    }

    var $tpDiv = $('<div class="time-picker'+ (settings.show24Hours ? '' : ' time-picker-12hours') +'"></div>');
    var $tpList = $('<ul></ul>');
    
    // Build the list.
    for(var i = 0; i < times.length; i++) {
      $tpList.append("<li>" + times[i] + "</li>");
    }
    $tpDiv.append($tpList);
    // Store element offset.
    var elmOffset = $(elm).offset();
    // Append the timPicker to the body and position it.
    $tpDiv.appendTo('body').css({'top':elmOffset.top, 'left':elmOffset.left}).hide();
    
    $("li", $tpList).unbind().mouseover(function() {
      $("li.selected", $tpDiv).removeClass("selected");  // TODO: only needs to run once.
      $(this).addClass("selected");
    }).mousedown(function() {
       tpOver = true;
    }).click(function() {
      setTimeVal(elm, this, $tpDiv, settings);
      tpOver = false;
    });
    
    // Store ananymous function in variable since it's used twice.
    var showPicker = function() {
      $tpDiv.show(); // Show picker.
      $tpDiv.mouseover(function() { // Have to use mouseover instead of mousedown because of Opera
        tpOver = true;
      }).mouseout(function() {
        tpOver = false;
      });
      $("li", $tpDiv).removeClass("selected");
      
      // Try to find a time in the list that matches the entered time.
      var time = this.value ? timeStringToDate(this.value, settings) : startTime;
      var startMin = startTime.getHours() * 60 + startTime.getMinutes();
      var min = (time.getHours() * 60 + time.getMinutes()) - startMin;
      var steps = Math.round(min / settings.step);
      var roundTime = normaliseTime(new Date(2001, 0, 0, 0, (steps * settings.step + (startMin)), 0));
      roundTime = (startTime < roundTime && roundTime < endTime) ? roundTime : startTime;
      
      var $matchedTime = $("li:contains(" + formatTime(roundTime, settings) + ")", $tpDiv);
      
      if ($matchedTime.length) {
        $matchedTime.addClass("selected");
        // Scroll to matched time.
        $tpDiv[0].scrollTop = $matchedTime[0].offsetTop;
      }
    };
    
    $(elm).unbind().focus(showPicker).click(showPicker)
    // Hide timepicker on blur
    .blur(function() {
      if (!tpOver && $tpDiv[0].parentNode) { // Don't remove when timePicker is clicked or when already removed
        $tpDiv.hide();
      }
    })
    
    // Key support
    .keypress(function(e) {
      switch (e.keyCode) {
        case 38: // Up arrow.
        case 63232: // Safari up arrow.
          var $selected = $("li.selected", $tpList);
          var prev = $selected.prev().addClass("selected")[0];
          if (prev) {
            $selected.removeClass("selected");
            $tpDiv[0].scrollTop = prev.offsetTop;
          }
          return false;
          break;
        case 40: // Down arrow.
        case 63233: // Safari down arrow.
          var $selected = $("li.selected", $tpList);
          var next = $selected.length ? $selected.next().addClass("selected")[0] : $("li:first").addClass("selected")[0];
          if (next) {
            $selected.removeClass("selected");
            $tpDiv[0].scrollTop = next.offsetTop;
          }
          return false;
          break;
        case 13: // Enter
          if (!$tpDiv.is(":hidden")) {
            var sel = $("li.selected", $tpList)[0];
            setTimeVal(elm, sel, $tpDiv, settings);
            return false;
          }
          break;
      }
    });
    
    // Helper function to get an inputs current time as Date object.
    // Returns a Date object.
    this.getTime = function() {
      return timeStringToDate(elm.value, settings);
    };
    // Helper function to set a time input.
    // Takes a Date object.
    this.setTime = function(time) {
      elm.value = formatTime(normaliseTime(time), settings);
      // Trigger element's change events.
      $(elm).change();
    };
    
  }; // End fn;   
  
  // Plugin defaults.
  $.fn.timePicker.defaults = {
    step:30,
    startTime: new Date(0, 0, 0, 0, 0, 0),
    endTime: new Date(0, 0, 0, 23, 30, 0),
    separator: ':',
    show24Hours: true
  };
  
  // Private functions.
  
  function setTimeVal(elm, sel, $tpDiv, settings) {
    // Update input field
    elm.value = $(sel).text();
    // Trigger element's change events.
    $(elm).change();
    // Keep focus for all but IE (which doesn't like it)
    if (!$.browser.msie) {
      elm.focus();
    }
    // Hide picker
    $tpDiv.hide();
  }
  
  function formatTime(time, settings) {
    var h = time.getHours();
    var hours = settings.show24Hours ? h : (((h + 11) % 12) + 1);
    var minutes = time.getMinutes();
    return formatNumber(hours) + settings.separator + formatNumber(minutes) + (settings.show24Hours ? '' : ((h < 12) ? ' AM' : ' PM'));
  }
  
	function formatNumber(value) {
		return (value < 10 ? '0' : '') + value;
	}
  
  function timeStringToDate(input, settings) {
    if (input) {
      var array = input.split(settings.separator);
      var hours = parseFloat(array[0]);
      var minutes = parseFloat(array[1]);
      var time = new Date(0, 0, 0, hours, minutes, 0);
      return normaliseTime(time);
    }
    return null;
  }
  
  /* Normalise time object to a common date. */
	function normaliseTime(time) {
		time.setFullYear(2001);
		time.setMonth(0);
		time.setDate(0);
		return time;
	}
  
})(jQuery);
