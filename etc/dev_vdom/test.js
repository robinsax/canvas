(function () {
	cv.loadStyle('someStyle');
	cv.import(['ui', 'api'], function () {

		var doThing = function doThing() {
			ui.createAlert(api.get('/current_alert'));
		};

		cv.export('test', {
			doThing: doThing
		});
	});
})();