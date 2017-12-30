#	coding utf-8
'''
Core request handling logic
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
	make_json, 
	register,
	logger,
	call_registered, 
	format_traceback
)
from ..model import create_session
from ..controllers import Page, get_controller
from .thread_context import *
from .assets import get_client_asset, render_template
from .. import __version__ as canvas_version, config

log = logger()

__all__ = [
	'handle_request'
]

SERVER_IDENTIFIER = f'Python/{python_version()} Werkzeug/{werkzeug_version} Canvas/{canvas_version}'

def handle_request(environ, start_response):
	req = BaseRequest(environ)
	cookie = None

	call_registered('callback:request_recieved', req)

	#	Either serve an asset or a controller
	try:
		if req.path.startswith('/assets/'):
			response = handle_asset_request(req)
		else:
			#	Get cookie
			cookie_data = req.cookies.get('canvas_session', None)
			if cookie_data is None:
				cookie = SecureCookie(secret_key=config['cookie_secret_key'].encode('utf-8'))
			else:
				cookie = SecureCookie.unserialize(cookie_data, config['cookie_secret_key'].encode('utf-8'))

			response = handle_controller_request(req, cookie)
	except BaseException as e:
		#	If it's here something is really fucked
		log_error(req, e, {'variant': 'Yikes!'}, level=log.critical)
		response = ('Internal Server Error', 500, {}, 'text/plain')

	remove_thread_context()

	#	Unpack response
	data, status, headers, mimetype = response

	#	Update headers to identify self
	headers['Server'] = SERVER_IDENTIFIER
	#	Thx. werkzeug
	response_obj = BaseResponse(**{
		'response': data,
		'status': status,
		'headers': headers,
		'mimetype': mimetype
	})
	#	Update headers to set cookie
	#	TODO: Do above via header
	if cookie is not None and cookie.should_save:
		response_obj.set_cookie('canvas_session', cookie.serialize())
	
	return response_obj(environ, start_response)

def log_error(req, error, ctx, level=log.error):
	#	These clog up context
	remove = []
	for k in ctx:
		if k.startswith('big_'):
			remove.append(k)
	for k in remove:
		del ctx[k]

	tb_str = format_traceback(error)
	ctx_str = pformat(ctx)
	level(os.linesep.join([
		f'Request error on: {req.path}',
		'-- Traceback --',
		tb_str,
		'-- Context --',
		ctx_str
	]))
	return tb_str

def handle_asset_request(req):
	path = req.path[8:]
	data = get_client_asset(path)

	#	Assert exists
	if data is None:
		return 'Not Found', 404, {}, 'text/plain'
	
	#	Guess mimetype
	mimetype = types_map.get('.' + path.split('.')[-1], 'text/plain')

	#	Return result
	#	TODO: Cache pragma header in debug
	return data, 200, {}, mimetype

def handle_controller_request(req, cookie):
	is_get = req.method == 'GET'
	is_api_request = req.path.startswith('/api/')
	
	#	Get parameters
	if is_get:
		params = req.args
	else:
		params = json.loads(req.get_data(as_text=True))
	params = WrappedDict(params, RequestParamError)

	#	Create session
	session = create_session()
	
	#	Wrap headers
	headers = WrappedDict(req.headers, HeaderKeyError)

	#	Collect request context
	ctx = {
		'cookie': cookie,
		'session': session,
		'request': params,
		'headers': headers,
		'big_3': (params, cookie, session)
	}
	call_registered('callback:context_create', ctx)
	register_thread_context(ctx)

	try:
		controller = get_controller(req.path)
		if isinstance(controller, Page):
			#	So we can change it dynamically
			ctx['page_name'] = controller.name

		call_registered('callback:pre_controller_dispatch', controller, ctx)

		addressed = params.get('__component__', None)
		if addressed is not None :
			#	Request was addressed to a component
			component = controller.components[addressed]
			call_registered('callback:pre_component_dispatch', component, ctx)
			response = component.handle_get(ctx) if is_get else component.handle_post(ctx)
		else:
			response = controller.get(ctx) if is_get else controller.post(ctx)

		#	Fix controller output
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
		if headers.get('X-Canvas-View-Request', None) == '1':
			#	To support P-R-G, we redirect the view by
			#	invoking an action in its JavaScript
			return make_json('success', {
				'action': 'redirect',
				'url': e.target
			})
		else:
			#	Return a normal redirect
			return '', e.code, {
				'Location': e.target
			}
	except ValidationErrors as e:
		log_error(req, e, ctx)
		return make_json('failure', {
			'errors': e.error_dict
		}, status=400)
	except HTTPException as e:
		error, error_desc, error_code = (e, e.desc, e.code)
	except BaseException as e:
		error, error_desc, error_code = (e, 'Internal Server Error', 500)
	
	error_data = {
		'code': error_code,
		'description': error_desc
	}
	ctx['error'] = error_data
	
	#	Log and make traceback
	tb_str = log_error(req, error, ctx)
	
	if is_api_request or not is_get:	
		if config['debug']:
			del ctx['error'] #TODO Wtf is going on with this dict
			error_data['debug_info'] = {
				'traceback': tb_str,
				'context': ctx
			}
		return make_json('error', error_data, status=error_code, default=lambda o: o.__repr__())
	else:
		#	TODO: Holy fuck!
		return render_template('pages/error.html', response=True, template_globals={
			**ctx,
			**{
				'debug_info': {
					'traceback': tb_str,
					'context': pformat(ctx)
				},
				'__ctx__': ctx,
				'__page__': {
					'collect_dependencies': lambda *args: (
						config['global_assets']['internal'],
						config['global_assets']['library']
					),
					'description': config['description']
				},
				'page_name': error_code
			}
		}, status=error_code)
