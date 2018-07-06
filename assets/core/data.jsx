/*
*	Data retrieval and caching. Integrates with views that depend on 
*	asynchronously requested data.
*/

const dataLog = new Logger('data');

class DataCache {
	/* A cache of retrieved data. */

	constructor(requestOptions) {
		if (typeof requestOptions == 'string') {
			requestOptions = {url: requestOptions};
		}
		this.requestOptions = requestOptions;

		this.data = {};
		//	Define the list of views which are using this data cache.
		this.views = [];
		this.callbacks = [];

		this.fetch();
	}

	alias(alias) {
		DataManager.instance.dataCaches[alias] = this;
		return this;
	}

	copy(alias) {
		let instance = new DataCache(this.requestOptions);
		DataManager.instance.dataCaches[alias] = instance;
		return instance;
	}

	fetch() {
		/* Refresh this cache. */
		(new Request(this.requestOptions)).success(this.completeFetch.bind(this));
		return this;
	}

	onceFetched(callback) {
		this.callbacks.push(callback);
		return this;
	}

	updateQuery(query) {
		dataLog.warn('updateQuery is deprecated, use query()');
		this.query(query);
	}

	query(query) {
		this.requestOptions.query = query;
		this.fetch();
		return this;
	}

	completeFetch(response) {
		/* Update the data in this cache and it's views. */
		if (typeof response == 'object') {
			this.data = response.data || {};
		}
		else {
			this.data = response;
		}

		for (let i = 0; i < this.views.length; i++) {
			this.views[i].data = this.data;
			this.views[i].onceFetched();
		}
		for (let i = 0; i < this.callbacks.length; i++) {
			this.callbacks[i](this.data);
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
		this.log = new Logger('data');

		DataManager.instance = this;
	}

	@exposedMethod
	dataCache(requestOptions) {
		this.log.warning('dataCache is depricated, use data()');
		return this.data(requestOptions);
	}
	
	@exposedMethod
	data(requestOptions) {
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
