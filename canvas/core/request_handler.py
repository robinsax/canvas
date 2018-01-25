#	coding utf-8
'''
The WSGI application definition.
'''

import os
import json

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
	logger,
	call_registered, 
	format_traceback
)

from ..model import create_session
from ..controllers import Page, get_controller
from .. import __version__ as canvas_version, config
from .thread_context import *
from .assets import get_client_asset, render_template
from . import create_json

log = logger()

__all__ = [
	'handle_request'
]

#	The server identifier string for the `Server`
#	header.
SERVER_IDENTIFIER = ' '.join([
	f'Python/{python_version()}',
	f'Werkzeug/{werkzeug_version}', 
	f'Canvas/{canvas_version}'
])

def handle_request(environ, start_response):
	'''
	The WSGI application, exported to the root package
	as `application`.

	Invokes either the controller or asset request handler,
	expecting them to return a tuple containing:
	```
	response, status, headers, mimetype
	```
	'''
	req = BaseRequest(environ)
	cookie = None

	#	Invoke pre-handling callbacks.
	call_registered('request_recieved', req)

	try:
		if req.path.startswith('/assets/'):
			#	Serve an asset.
			response = _handle_asset_request(req)
		else:
			#	Encode the configured secret key to bytes.
			secret_key = config['cookie_secret_key'].encode('utf-8')

			#	Get the cookie if there is one.
			cookie_data = req.cookies.get('canvas_session', None)
			if cookie_data is None:
				#	Create an empty cookie.
				cookie = SecureCookie(secret_key=secret_key)
			else:
				#	Parse the cookie data.
				cookie = SecureCookie.unserialize(cookie_data, secret_key)

			#	Invoke controller dispatch.
			response = _handle_controller_request(req, cookie)
	except BaseException as e:
		#	We can't serve at all. A common cause is an
		#	error in the base template.
		_log_error(req, e, dict(), level=log.critical)
		response = ('Internal Server Error', 500, {}, 'text/plain')

	#	Delete the thread-id to request context mapping.
	remove_thread_context()

	#	Unpack response.
	data, status, headers, mimetype = response

	#	Add identification header.
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
		response_obj.set_cookie('canvas_session', cookie.serialize())
	
	call_registered('response_dispatch', response_obj)

	#	Invoke the response object.
	return response_obj(environ, start_response)

def _log_error(req, error, ctx, level=log.error):
	'''
	Log a request error and return the traceback
	string to be sent to the client if debug mode
	is enabled.
	'''
	#	Remove shortcuts from context.
	remove = []
	for k in ctx:
		if k.startswith('big_'):
			remove.append(k)
	for k in remove:
		del ctx[k]

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
	#	Remove the `/asset/` prefix.
	path = req.path[8:]

	#	Get the asset contents.
	data = get_client_asset(path)
	#	Assert existance.
	if data is None:
		return 'Not Found', 404, {}, 'text/plain'
	
	#	Evaluate the mimetype.
	mimetype = types_map.get('.' + path.split('.')[-1], 'text/plain')

	#	TODO: Cache control
	return data, 200, {}, mimetype

def _handle_controller_request(req, cookie):
	#	Parse request context.
	is_get = req.method == 'GET'
	is_api_request = req.path.startswith('/api/')
	
	#	Create parameters dictionary.
	if is_get:
		params = req.args
	else:
		try:
			params = json.loads(req.get_data(as_text=True))
		except:
			#	TODO: Better.
			params = {}
	params = WrappedDict(params, RequestParamError)

	#	Create database session.
	session = create_session()
	
	#	Wrap headers.
	headers = WrappedDict(req.headers, HeaderKeyError)

	#	Create request context.
	ctx = {
		'cookie': cookie,
		'session': session,
		'request': params,
		'headers': headers,
		'big_3': (params, cookie, session)
	}
	#	Allow callbacks to modify the context.
	call_registered('context_create', ctx)

	#	Add the thread-id, request context mapping.
	register_thread_context(ctx)

	try:
		#	Retrieve the controller
		controller = get_controller(req.path)
		if isinstance(controller, Page):
			#	The template reads this to populate the `title`
			#	tag so to allow it to be set dynamically.
			ctx['page_title'] = controller.title

		#	Allow callbacks to raise exceptions if there
		#	is something wrong with the context.
		call_registered('pre_controller_dispatch', controller, ctx)

		#	Check if the request as addressed to a component of
		#	the controller, then either invoke the controller or
		#	that component.
		addressed = params.get('__component__', None)
		if addressed is not None :
			#	Request was addressed to a component.
			component = controller.components[addressed]

			#	Allow callbacks to raise exceptions if there
			#	is something wrong with the context.
			call_registered('pre_component_dispatch', component, ctx)

			#	Dispatch component.
			response = component.handle_get(ctx) if is_get else component.handle_post(ctx)
		else:
			#	Dispatch controller.
			response = controller.get(ctx) if is_get else controller.post(ctx)

		#	Controllers won't nessesarily return a complete 
		#	response tuple. Populate with defaults if they dont.
		if not isinstance(response, (tuple, list)):
			response = (response,)
		if len(response) == 4:
			return response
		elif len(response) == 3:
			return response + ('text/html',)
		elif len(response) == 2:
			return response + ({}, 'text/html')
		else:
			return response + (200, {}, 'text/html')

	except _Redirect as e:
		#	A redirection occured.
		if headers.get('X-Canvas-View-Request', None) == '1':
			#	This request was an in-browser AJAX so a normal
			#	redirect won't work; invoke a core action.
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
		#	A model constraint was violated.
		_log_error(req, e, ctx)

		#	Return the canonical model-constraint-violation
		#	response.
		return create_json('failure', {
			'errors': e.error_dict
		}, status=400)
	except HTTPException as e:
		#	A status-coded exception was raised.
		error, error_desc, error_code = (e, e.desc, e.code)
	except BaseException as e:
		#	An unexpected exception was raised.
		error, error_desc, error_code = (e, 'Internal Server Error', 500)
	
	#	Create the error data
	error_data = {
		'code': error_code,
		'description': error_desc
	}
	#	...and add to context.
	ctx['error'] = error_data
	
	#	Log the error and retrieve the traceback string.
	tb_str = _log_error(req, error, ctx)
	
	#	TODO: This dictionary is out of control.

	if is_api_request or not is_get:
		#	Client is expecting JSON.
		if config['debug']:
			#	We are going to send the context as part
			#	of the error data, remove the reference
			#	to prevent a circular reference.
			del ctx['error']

			#	Add the debug information to the error response.
			error_data['debug_info'] = {
				'traceback': tb_str,
				'context': ctx
			}
		return create_json('error', error_data, **{
			'status': error_code,
			#	This will guarenteed serialize anything.
			'default_serializer': lambda o: o.__repr__()
		})
	else:
		#	Client is expecting a page; render the 
		#	error template.
		return render_template('pages/error.html', response=True, template_params={
			**ctx,
			**{
				'debug_info': {
					'traceback': tb_str,
					'context': pformat(ctx)
				},
				#	Emulate a page for the base template.
				'__page__': {
					'collect_dependencies': lambda *args: (
						config['client_dependencies']['dependencies'],
						config['client_dependencies']['library_dependencies']
					),
					'description': config['description']
				},
				'page_title': error_code
			}
		}, status=error_code)
