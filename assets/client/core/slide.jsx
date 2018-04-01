@part
class SlidePart {
	constructor(core) {
		core.addInspector((check) => {
			this.registerSlides(check);
		})
	}

	registerSlides(check) {
		check.reduce('a.slide').on('click', (el, event) => {
			event.preventDefault();
			let targetY = tk(el.attr('href')).offset().y;
			let html = tk('html').first(false);

			let time = el.attr('cv-time') || 500,
				start = html.scrollTop,
				speed = (targetY - start)/time
			
			tk.transition((time) => {
				return (html.scrollTop = (start + (speed*time))) < targetY;
			});
		})
	}
}