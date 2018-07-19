/*
*	Asynchronous request dispatch, processing, and callback API.
*/

const requestLog = new Logger('requests');
const formatFormData = (name, type, data) => {
return `--canvas_blob
Content-Disposition: form-data; name="file"; filename="${name}";
Content-Type: ${type}

${data}

--canvas_blob--`
}


class Request {
	/* An request context that manages retrieval and callbacks. */

	constructor(options) {
		/*
		*	Create and send a new `Request`. Canonically this is done via the
		*	exposed `request` method on the global `canvas`/`cv` object.
		*	`options` can be either a string containing a URL to send a `GET`
		*	request, or a map containing:
		*		* `url` - The target URL (required)
		*		* `method` - The request method (default `GET`)
		*		* `query` - A map containing the query parameters (optional)
		*		* `success` - A success callback (optional)
		*		* `failure` - A failure callback (optional)
		*		* `json` - A JSON-like object for the request body (optional)
		*		* `file` - A file object to upload (optional)
		*		* `headers` - A key, value header map (optional)
		*/
		//	Handle trivial request definition.
		if (typeof options == 'string') options = {url: options, method: 'get'};
		this.options = options;
		
		//	Store callback lists.
		this.successCallbacks = options.success ? [options.success] : [];
		this.failureCallbacks = options.failure ? [options.failure] : [];

		//	Resolve full URL.
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
		this.xhrObject.onreadystatechange = this.checkRequestState.bind(this);
		this.xhrObject.open(method.toUpperCase(), fullURL, true);
		this.xhrObject.setRequestHeader('X-cv-View', 1);

		this.logRepr = method + ' ' + fullURL;
		requestLog.info('Sent ' + this.logRepr);
		this.serializeBody(options, (mimetype, data) => {
			this.xhrObject.setRequestHeader('Content-Type', mimetype);
			this.xhrObject.send(data);
		});
	}

	checkRequestState() {
		/* Check the request state, handling a return if it occurred. */
		if (this.xhrObject.readyState != 4) return;

		//	Log.
		requestLog.info('Received ' + this.logRepr + ' ' + this.xhrObject.status);

		//	Process the response body.
		this.response = this.processResponse({
			status: this.xhrObject.status,
			mimetype: this.xhrObject.getResponseHeader('Content-Type'),
			pureData: this.xhrObject.responseText
		});
		
		//	Invoke the appropriate callback set.
		if (this.response.status < 400) {
			//	Dispatch success callbacks.
			if (this.successCallbacks.length == 0) {
				requestLog.warning('Unhandled request success for ' + this.options.url);
			}
			for (var i = 0; i < this.successCallbacks.length; i++) {
				this.successCallbacks[i](this.response.data, this.response.status);
			}
		}
		else {
			//	Dispatch failure callbacks.
			if (this.failureCallbacks.length == 0) {
				requestLog.warning('Unhandled request failure for ' + this.options.url);
			}
			for (var i = 0; i < this.failureCallbacks.length; i++) {
				this.failureCallbacks[i](this.response.data, this.response.status);
			}
		}
	}

	serializeBody(options, callback) {
		/* Serialize and return a request body given `options`. */
		//	TODO: Support more types or provide API.
		if (options.json) {
			requestLog.debug(options.json);
			callback('application/json', JSON.stringify(options.json));
		}
		else if (options.file) {
			let reader = new FileReader();
			reader.onload = event => {
				callback(
					'multipart/form-data; boundary=canvas_blob', 
					formatFormData(options.file.name, options.file.type, event.target.result)
				);
			}
			reader.readAsDataURL(options.file);
		}
		else {
			callback('', '');
		}
	}

	processResponse(response) {
		/* Deserialize the response body. */
		//	TODO: Support more types or provide API.
		switch (response.mimetype) {
			case 'application/json':
			case 'text/json':
				response.data = JSON.parse(response.pureData);
				requestLog.debug(response.data);
				break;
			default:
				requestLog.warning('Unknown mimetype ' + response.mimetype);
				response.data = response.pureData;
				break;
		}
		return response;
	}

	success(callback) {
		/* Add a success callback. */
		if (this.response) this.invokeCallback(callback);
		else this.successCallbacks.push(callback);

		return this;
	}

	failure(callback) {
		/* Add a failure callback. */
		if (this.response) this.invokeCallback(callback);
		else this.failureCallbacks.push(callback);

		return this;
	}
}

@coreComponent
class RequestFactory {
	/* The request API exposure. */

	@exposedMethod
	request(options, url=null, json=null) {
		/*
		*	Create, send, and return a new `Request`. See the `Request`
		*	constructor for the `options` specification.
		*/
		if (typeof options == 'string') {
			options = {url: options};
		}
		if (url) {
			options.method = options.url;
			options.url = url;
		}
		if (json) {
			options.json = json;
		}
		return new Request(options);
	}
}