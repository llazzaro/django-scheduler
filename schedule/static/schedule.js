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
