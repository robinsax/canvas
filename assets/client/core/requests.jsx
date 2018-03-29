@part
class RequestPart {
	constructor(core) {
		this.core = core;
	
		core.request = (method='POST', route=null) => this.request(method, route);
	}

	request(method, route) {
		if (!route) {
			route = this.core.route;
		}

		return tk.request(method, route)
			.header('X-cv-View', '1')
			.failure(() => {
				this.core.flashMessage = 'An error occured';
			});
	}
}