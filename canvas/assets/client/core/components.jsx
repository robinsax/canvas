@part
class ComponentPart {
	constructor(core){
		this.route = core.route;

		core.component = this.component;
	}

	component(...routes){
		return (ComponentClass) => {
			let load = routes.length == 0;
			tk.iter(routes, (route) => {
				if (route == this.route){
					load = true;
				}
			});

			if (load){
				let instance = new ComponentClass;
				tk.log('Created component', instance);
				
				if (instance.initDOM) {
					tk.init(() => { instance.initDOM(); });
				}
			}
		}
	}
}