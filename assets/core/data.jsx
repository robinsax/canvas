/*
*	Data retrieval and caching. Integrates with views that depend on 
*	asynchronously requested data.
*/

class DataCache {
	/* A cache of retrieved data. */

	constructor(requestOptions) {
		this.requestOptions = requestOptions;

		this.data = null;
		//	Define the list of views which are using this data cache.
		this.views = [];

		this.fetch();
	}

	fetch() {
		(new Request(this.requestOptions)).success(this.completeFetch.bind(this));
	}

	completeFetch(data) {
		this.data = data;
		for (var i = 0; i < this.views.length; i++) {
			this.views[i].data = data;
		}
	}

	addView(view) {
		this.views.push(view);
	}
}

@coreComponent
class DataManager {
	constructor() {
		this.dataCaches = {};
	}

	@exposedMethod
	fetch(requestOptions) {
		//	TODO: Better keying.
		let key = typeof requestOptions == 'string' ? requestOptions : JSON.stringify(requestOptions);
		let existing = this.dataCaches[key];
		if (existing) {
			return existing;
		}
		else {
			return this.dataCaches[key] = new DataCache(requestOptions);
		}
	}
}
