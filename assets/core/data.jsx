/*
*	Data retrieval and caching. Integrates with views that depend on 
*	asynchronously requested data.
*/

class DataCache {
	/* A cache of retrieved data. */

	constructor(requestOptions) {
		this.requestOptions = requestOptions;

		this.data = {};
		//	Define the list of views which are using this data cache.
		this.views = [];

		this.fetch();
	}

	alias(alias) {
		DataManager.instance.dataCaches[alias] = this;
	}

	fetch() {
		/* Refresh this cache. */
		(new Request(this.requestOptions)).success(this.completeFetch.bind(this));
	}

	completeFetch(response) {
		/* Update the data in this cache and it's views. */
		if (typeof response == 'object') {
			this.data = response.data;
		}
		else {
			this.data = response;
		}

		for (var i = 0; i < this.views.length; i++) {
			this.views[i].data = this.data;
			this.views[i].onceFetched();
		}
	}

	addView(view) {
		/* Add a view to this cache, to depend on it's data. */
		this.views.push(view);
	}
}

@coreComponent
class DataManager {
	/* The data caching API exposure. */

	constructor() {
		//	Create a request representation to DataCache map.
		this.dataCaches = {};

		DataManager.instance = this;
	}

	@exposedMethod
	dataCache(requestOptions) {
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

	@exposedMethod
	fetch(requestOptions) {
		/* 
		*	Retrieve a `DataCache` for the given request. 
		*	::requestOptions The request specification as passed to the 
		*		request constructor.
		*/
		//	TODO: Better keying.
		let key = typeof requestOptions == 'string' ? requestOptions : JSON.stringify(requestOptions);
		let existing = this.dataCaches[key];
		if (existing) {
			existing.fetch();
			return existing;
		}
		else {
			return this.dataCaches[key] = new DataCache(requestOptions);
		}
	}
}
