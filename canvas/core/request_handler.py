#	coding utf-8
'''
Base request handling logic and the WSGI application definition.
'''

import os

from json.decoder import JSONDecodeError
from platform import python_version
from mimetypes import types_map
from pprint import pformat

from werkzeug import __version__ as werkzeug_version
from werkzeug.wrappers import BaseRequest, BaseResponse
from werkzeug.contrib.securecookie import SecureCookie

from ..exceptions import (
	RequestParamError, 
	HeaderKeyError,
	ValidationErrors,
	HTTPException,
	_Redirect
)
from ..utils import (
	WrappedDict,
	register,
	get_registered,
	logger,
	call_registered,
	format_traceback,
	deserialize_json,
	serialize_json
)
from ..model import create_session
from ..controllers import Page, get_controller
from .. import __version__ as canvas_version, config
from .thread_context import *
from .assets import (
	get_client_asset, 
	render_template
)
from .cache_control import *
from . import create_json

#	Create a logger.
log = logger(__name__)

#	Declare exports.
__all__ = [
	'handle_request'
]

#	Create the server identifier string provided in the `Server` header.
SERVER_IDENTIFIER = ' '.join([
	f'Python/{python_version()}',
	f'Werkzeug/{werkzeug_version}', 
	f'Canvas/{canvas_version}'
])
#	The key under which the cookie session is stored.
COOKIE_KEY = 'canvas_session'

def handle_request(environ, start_response):
	'''
	The callable WSGI application.

	Invokes either the controller or asset request handler, expecting them to 
	return a tuple containing:
	```
	response, status, headers, mimetype
	```
	'''
	req = BaseRequest(environ)
	cookie = None

	#	Invoke pre-handling callbacks.
	call_registered('request_received', req)

	try:
		if req.path.startswith('/assets/'):
			#	Serve an asset.
			response = _handle_asset_request(req)
		else:
			#	Dispatch a controller.

			#	Encode the configured secret key to bytes.
			secret_key = config['cookie_secret_key'].encode('utf-8')

			#	Retrieve the cookie if there is one.
			cookie_data = req.cookies.get(COOKIE_KEY, None)
			if cookie_data is None:
				#	Create an empty cookie.
				cookie = SecureCookie(secret_key=secret_key)
			else:
				#	Parse the cookie data.
				cookie = SecureCookie.unserialize(cookie_data, secret_key)

			#	Invoke controller dispatcher.
			response = _handle_controller_request(req, cookie)
	except BaseException as e:
		#	We can't serve at all. A common cause is an error in the base 
		#	template.
		_on_error(req, e, {}, level=log.critical)
		response = ('Internal Server Error', 500, {}, 'text/plain')

	#	Delete the request context to thread ID mapping if there is one.
	remove_thread_context()

	#	Unpack the response.
	data, status, headers, mimetype = response

	#	Add the `Server` authentication header.
	headers['Server'] = SERVER_IDENTIFIER

	#	Create the response object.
	response_obj = BaseResponse(**{
		'response': data,
		'status': status,
		'headers': headers,
		'mimetype': mimetype
	})

	if cookie is not None and cookie.should_save:
		#	Set the cookie.
		response_obj.set_cookie(COOKIE_KEY, cookie.serialize())
	
	call_registered('pre_response_dispatch', response_obj)

	#	Invoke the response callable.
	return response_obj(environ, start_response)

def _on_error(req, error, ctx, level=log.error):
	'''
	Log a request error and invoke the error callback.
	
	Return the traceback string to be sent to the client if debug mode is 
	enabled.
	'''
	#	Remove shortcuts from context.
	remove = []
	for k in ctx:
		if k.startswith('big_'):
			remove.append(k)
	for k in remove:
		del ctx[k]

	#	Suppress huge inputs.
	if 'request' in ctx:
		request = ctx['request']
		remove = []
		for key, value in request.items():
			#	TODO: Configure.
			if isinstance(value, str) and len(value) > 500:
				remove.append(key)
		for key in remove:
			request[key] = f'{request[key][:500]}...'

	#	Invoke callbacks individually with error protection.
	for callback in get_registered('request_error'):
		try:
			callback(error, ctx)
		except BaseException as e:
			#	That's too bad.
			log.critical(f'Request error callback {callback.__name__} failed: '
					+ f'{e.__class__.__name__}: {str(e)}')

	#	Format and log.
	tb_str = format_traceback(error)
	ctx_str = pformat(ctx)
	level(os.linesep.join([
		f'Request error on: {req.path}',
		'-- Traceback --',
		tb_str,
		'-- Context --',
		ctx_str
	]))

	#	Return the formatted traceback string.
	return tb_str

def _handle_asset_request(req):
	'''
	Handle an asset retrieval request.
	'''
	#	Assert asset must be served.
	if not config['debug'] and 'If-Modified-Since' in req.headers:
		if is_cache_valid(req.headers['If-Modified-Since']):
			#	Return a `Not Modified` status.
			return '', 304, {}, 'text/plain'

	#	Remove the `/asset/` prefix.
	path = req.path[8:]

	#	Retrieve the asset.
	data = get_client_asset(path)

	#	Assert existance.
	if data is None:
		return 'Not Found', 404, {}, 'text/plain'
	
	#	Evaluate the mimetype.
	mimetype = types_map.get('.' + path.split('.')[-1], 'text/plain')

	#	TODO: Test cache control.
	return data, 200, get_cache_control_headers(), mimetype

def _handle_controller_request(req, cookie):
	#	Parse request context.
	is_get = req.method == 'GET'
	is_api_request = req.path.startswith('/api/')
	
	#	Create parameters dictionary.
	if is_get:
		params = req.args
	else:
		body = req.get_data(as_text=True)
		if len(body) == 0:
			params = {}
		else:
			try:
				params = deserialize_json(body)
			except JSONDecodeError:
				return 'Expecting JSON', 400, {}, 'text/plain'
	params = WrappedDict(params, RequestParamError)

	#	Create a database session.
	session = create_session()
	
	#	Wrap the headers dictionary.
	headers = WrappedDict(req.headers, HeaderKeyError)

	#	Create the request context.
	ctx = {
		'cookie': cookie,
		'session': session,
		'request': params,
		'headers': headers,
		'big_3': (params, cookie, session)
	}
	#	Allow callbacks to modify.
	call_registered('context_created', ctx)

	#	Add the thread ID request context mapping entry.
	register_thread_context(ctx)

	try:
		#	Retrieve the controller.
		controller = get_controller(req.path)

		#	Allow callbacks to raise exceptions if there is something wrong 
		#	with the context.
		call_registered('pre_controller_dispatch', controller, ctx)

		#	Dispatch controller.
		response = controller.get(ctx) if is_get else controller.post(ctx)

		#	Controllers won't nessesarily return a complete response tuple. 
		#	Populate with defaults if they dont.
		if not isinstance(response, (tuple, list)):
			response = [response,]
		else:
			response = list(response)
		
		if len(response) == 4:
			return response
		elif len(response) == 3:
			return response + ['text/plain']
		elif len(response) == 2:
			return response + [{}, 'text/plain']
		else:
			return response + [200, {}, 'text/plain']

	except _Redirect as e:
		#	A redirection occured.
		if headers.get('X-Canvas-View-Request', None) == '1':
			#	This request was an in-browser AJAX so a normal redirect won't 
			#	work; invoke a core action.
			return create_json('success', {
				'action': 'redirect',
				'url': e.target
			})
		else:
			#	Return a standard redirect response.
			return '', e.code, {
				'Location': e.target
			}, ''
	except ValidationErrors as e:
		#	Return the canonical model-constraint-violation response.
		data = {}
		if e.summary is not None:
			data['error_summary'] = e.summary
		if e.error_dict is not None:
			data['errors'] = e.error_dict
		return create_json('failure', data, status=422)
	except HTTPException as e:
		#	A status-coded exception was raised.
		error, error_desc, error_code = (e, e.desc, e.code)
	except BaseException as e:
		#	An unexpected exception was raised.
		error, error_desc, error_code = (e, 'Internal Server Error', 500)
	
	#	Create the error data.
	error_data = {
		'code': error_code,
		'description': error_desc
	}
	#	...and add it to context.
	ctx['error'] = error_data
	
	#	Log the error and retrieve the traceback string.
	tb_str = _on_error(req, error, ctx)
	
	#	TODO: This dictionary is out of control.

	if is_api_request or not is_get:
		#	Client is expecting JSON.
		if config['debug']:
			#	We are going to send the context as part of the error data, 
			#	remove the reference to prevent a circular reference.
			del ctx['error']

			#	Add the debug information to the error response.
			error_data['debug_info'] = {
				'traceback': tb_str,
				'context': ctx
			}
		return create_json('error', error_data, **{
			'status': error_code,
			#	This will guarenteed serialize anything.
			'fallback_serializer': lambda o: o.__repr__()
		})
	else:
		#	Client is expecting a page; render the error template.
		return render_template('pages/error.html', response=True, template_params={
			**ctx,
			**{
				'debug_info': {
					'traceback': tb_str,
					'context': pformat(ctx)
				},
				#	Emulate a page for the base template.
				'__page__': {
					**config['client_dependencies'],
					**{
						'description': config['description']
					}
				}
			}
		}, status=error_code)
