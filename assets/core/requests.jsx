/*
*	Asynchronous requests dispatch.
*/

const requestLog = new Logger('requests');

class Request {
	/* An request context that manages retrieval and callbacks. */

	constructor(options) {
		//	Handle trivial request definition.
		if (typeof options == 'string') options = {url: options, method: 'get'};
		this.options = options;
		
		//	Process options.
		this.successCallbacks = options.success ? [options.success] : [];
		this.failureCallbacks = options.failure ? [options.failure] : [];
		let fullURL = options.url;
		if (options.query) {
			queryParts = [];
			for (let key in options.query) {
				queryParts.push(key + '=' + encodeURIComponent(options.query[key]));
			}
			fullURL = fullURL + '?' + queryParts.join('&');
		}
		let method = options.method || 'get';

		//	Define the response holder.
		this.response = null;
		//	Create and dispatch the request.
		this.xhrObject = new XMLHttpRequest();
		this.xhrObject.onreadystatechange = () => {
			if (this.xhrObject.readyState != 4) return;

			this.response = this.processResponse({
				status: this.xhrObject.status,
				mimetype: this.xhrObject.getResponseHeader('Content-Type'),
				pureData: this.xhrObject.responseText,
			});
			
			requestLog.info('Received ' +  + method + ' ' + fullURL + ' ' + this.response.status);
			requestLog.info(this.response.data);
			if (this.response.status > 299) {
				//	Dispatch success callbacks.
				if (this.successCallbacks.length == 0) {
					requestLog.warning('Unhandled request success for ' + options.url);
				}
				for (var i = 0; i < this.successCallbacks.length; i++) {
					this.invokeCallback(this.successCallbacks[i]);
				}
			}
			else {
				//	Dispatch failure callbacks.
				if (this.failureCallbacks.length == 0) {
					requestLog.warning('Unhandled request failure for ' + options.url);
				}
				for (var i = 0; i < this.failureCallbacks.length; i++) {
					this.invokeCallback(this.failureCallbacks[i]);
				}
			}
		}
		this.xhrObject.open(method.toUpperCase(), fullURL, true);
		this.xhrObject.send(this.getSerializedBody(options));
		requestLog.info('Sent ' + method + ' ' + fullURL);
	}

	getSerializedBody(options) {
		//	TODO: Support more types or provide API.
		if (options.json) {
			return JSON.stringify(options.json);
		}
		
		return '';
	}

	success(callback) {
		if (this.response) this.invokeCallback(callback);
		else this.successCallbacks.push(callback);
	}

	failure(callback) {
		if (this.response) this.invokeCallback(callback);
		else this.failureCallbacks.push(callback);
	}

	invokeCallback(callback) {
		try {
			callback(this.response.data, this.response.status);
		}
		catch (ex) {
			requestLog.critical('Error in request callback: ' + ex);
		}
	}

	processResponse(response) {
		switch (response.mimetype) {
			case 'application/json':
			case 'text/json':
				response.data = JSON.parse(response.pureData);
				break;
			default:
				requestLog.warning('Unknown mimetype ' + response.mimetype);
				response.data = response.pureData;
				break;
		}
		return response;
	}
}

@coreComponent
class RequestFactory {
	@exposedMethod
	request(options) {
		return new Request(options);
	}
}