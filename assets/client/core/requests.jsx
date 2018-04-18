@part
class RequestPart {
	constructor() {	
		core.request = (method='POST', route=null) => this.request(method, route);
	}

	request(method, route) {
		if (!route) {
			route = core.route;
		}

		return tk.request(method, route)
			.header('X-cv-View', '1')
			.failure(() => {
				core.flashMessage = 'An error occured';
			});
	}
}