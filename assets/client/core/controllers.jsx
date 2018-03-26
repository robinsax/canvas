@part
class ControllerPart {
	constructor(core) {	
		this.core = core;
		
		core.controller = (...routes) => this.controller(routes);
	}
	
	initDOM() {
		tk.iter(this.controllers, (controller) => {
			controller.initDOM();
		});
	}

	controller(routes) {
		return (ControllerClass) => {
			let load = false;
			tk.iter(routes, (route) => {
				if (cv.route == route){
					load = true;
					return false;
				}
			});

			if (!load) { return; }

			this.core.onceReady(() => {
				tk.log('Loaded controller ' + ControllerClass.name);
				new ControllerClass();
			});
		}
	}
}
