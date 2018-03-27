@part
class RoutingPart {
	constructor(core) {
		this.core = core;

		core.routing = (routing) => this.routing(routing);
	}

	routing(routing) {
		tk.iter(routing, (route, definition) => {
			if (route == '*' || route == this.core.route){
				tk.iter(definition, (selector, views) => {
					tk.iter(views, (ViewClass) => {
						this.core.view.create(selector, ViewClass);
					});
				});
			}
		});
	}
}
