$(document).ready(function () {
  var $wrapper = $('#wrapper');
  $('[data-toggle="offcanvas"]').click(function () {
    $wrapper.toggleClass('toggled');
    if ($wrapper.hasClass('toggled')) {
      Cookies.set('sidebar-state', 'close');
    } else {
      Cookies.set('sidebar-state', 'open');
    }
  });
});
