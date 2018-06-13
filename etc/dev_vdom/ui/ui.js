(function () {
  cv.loadStyle('ui.ui');

  var greet = function greet() {
    return console.log('%cHello World', 'color: blue');
  };

  cv.export('ui/ui', {
    greet: greet
  });
})();