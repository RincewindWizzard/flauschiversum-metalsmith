$(function() {
  var aspect_ratio = 0.75
  function resizeImages() {
    $('.slideshow a').width( $('.slideshow').width() + 1)
    $('.slideshow').each(function() {
      var width = $(this).width()
      $(this).height(width * aspect_ratio)
    })
  }
  resizeImages()
  $(window).resize(function() {
    resizeImages()
  });
})
