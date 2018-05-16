@part
class RequestPart {
	constructor() {	
		core.request = this.request.bind(this);
		core.fetchOnto = this.fetchOnto.bind(this);
	}

	request(method='post', route=null) {
		if (!route) {
			route = core.route;
		}

		return tk.request(method, route)
			.header('X-cv-View', '1')
			.failure(() => {
				core.flashMessage = 'An error occured';
			});
	}

	fetchOnto(url, obj, prop) {
		this.request('get', url)
			.success(resp => obj[prop] = resp.data)
			.send();
	}
}