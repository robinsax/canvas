@part
class PagePart {
	constructor(core) {
		this.pages = [];
		
		core.page = (...routes) => this.page(routes);
	}

	initDOM() {
		tk.iter(this.pages, (page) => {
			page.initDOM();
		});
	}

	page(routes) {
		return (PageClass) => {
			let load = false;
			tk.iter(routes, (route) => {
				if (cv.route == route){
					load = true;
					return false;
				}
			});

			if (!load) { return; }

			let instance = new PageClass();
			tk.log('Loaded page ' + PageClass.constructor.name);
			this.pages.push(instance);
		}
	}
}