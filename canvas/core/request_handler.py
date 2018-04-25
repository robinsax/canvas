#	coding utf-8
'''
The canvas WSGI application implementation.
'''

from mimetypes import types_map
from platform import python_version

from werkzeug import BaseRequest, BaseResponse
from werkzeug.contrib.securecookie import SecureCookie

from ..exceptions import (
	HTTPException, 
	ValidationErrors,
	InternalServerError,
	NotFound,
	UnsupportedVerb,
	OversizeEntity,
	UnsupportedMediaType
)
from ..utils import logger, format_exception
from ..configuration import config
from ..callbacks import (
	define_callback_type, 
	invoke_callbacks
)
from ..controllers import Endpoint
from .dictionaries import AttributedDict, RequestParameters
from .plugins import get_path_occurrences
from .model import create_session
from .routing import resolve_route
from .request_parsers import parse_request
from .request_context import RequestContext, RouteString
from .request_errors import get_error_response
from .responses import create_json
from .styles import compile_less
from .node_interface import transpile_jsx
from .. import __version__ as canvas_version

log = logger(__name__)

_identifier = 'canvas/%s Python/%s'%(
	canvas_version,
	python_version()
)
_asset_cache = dict()

define_callback_type('request_received', arguments=[RequestContext], ext=True)

def parse_response_tuple(tpl):
	if not isinstance(tpl, (list, tuple)):
		tpl = (tpl,)
	
	corrected = ['', 200, None, 'text/plain']
	for i in range(len(tpl)):
		corrected[i] = tpl[i]
	
	data, status, headers, mimetype = corrected
	if headers is None:
		headers = dict()

	response_object = BaseResponse(
		response=data,
		status=status,
		headers=headers,
		mimetype=mimetype
	)

	return response_object

def report_error(ex, context=None):
	should_report = (
		not isinstance(ex, HTTPException) or
		(
			(ex.status_code > 499 or config.development.log_client_errors) and
			not (isinstance(ex, InternalServerError) and ex.reraise)
		)
	)
	if should_report:
		log.error(format_exception(ex))

def retrieve_asset(path, recall=False):
	occurrences = get_path_occurrences('assets', 'client', path[1:])
	if len(occurrences) == 0:
		return None

	with open(occurrences[-1], 'rb') as asset_file:
		asset_data = asset_file.read()
	
	if recall:
		if path.endswith('.less'):
			asset_data = compile_less(asset_data.decode())
		if path.endswith('.jsx'):
			asset_data = transpile_jsx(asset_data)
		
	if not config.development.debug:
		_asset_cache[path] = asset_data
	return asset_data

def serve_controller(request):
	#	Resolve path.
	route = request.path
	controller, variables = resolve_route(route)

	#	Resolve verb.
	verb = request.method.lower()
	if verb not in controller.__verbs__:
		raise UnsupportedVerb(verb, [v.upper() for v in controller.__verbs__])
	handler = getattr(controller, 'on_{}'.format(verb))

	#	Resolve parameters.
	if verb == 'get':
		request_parameters = RequestParameters(request.args)
	else:
		body_size = int(request.headers.get('Content-Length', 0))
		content_type = request.headers.get('Content-Type')
		expected_type = getattr(controller, '__expects__', 'json')

		if body_size > config.security.max_bytes_receivable:
			raise OversizeEntity(body_size)
		elif body_size == 0:
			request_parameters = RequestParameters() if 'json' in expected_type else None
		else:
			should_assert = content_type and expected_type != '*'

			if should_assert and expected_type not in content_type:
				raise UnsupportedMediaType('Expected %s'%expected_type.upper())

			request_parameters = parse_request(request.get_data(as_text=True), content_type)

	#	Resolve cookie.
	cookie_key, secret = config.security.cookie_key, config.security.cookie_secret
	secret = secret.encode('utf-8')

	cookie_data = request.cookies.get(cookie_key, None)
	if cookie_data:
		cookie = SecureCookie.unserialize(cookie_data, secret)
	else:
		cookie = SecureCookie(secret_key=secret)

	route_desc = RouteString(route)
	route_desc.set_variables(variables)

	#	Create context and handle.
	context = RequestContext({
		'cookie': cookie,
		'session': create_session(),
		'request': request_parameters,
		'headers': request.headers,
		'route': route_desc,
		'verb': verb,
		'url': request.url
	})
	RequestContext.put(context)

	def cleanup(response=None):
		RequestContext.pop()

		if response and cookie.should_save:
			response.set_cookie(cookie_key, cookie.serialize())
	
	try:
		invoke_callbacks('request_received', context)

		response = handler(context)
	except ValidationErrors as ex:
		report_error(ex, context)
		#	TODO: XML plugin should be able to override.
		data = ex.dictize()
		data.update({
			'code': 422,
			'title': 'Validation Errors'
		})
		response = create_json('failure', data, 422, None)
	except BaseException as ex:
		cleanup()
		report_error(ex, context)
		diag_ex = ex
		if not isinstance(ex, HTTPException):
			ex = InternalServerError(True)
		ex.diag = (diag_ex, context)
		raise ex
	
	response = parse_response_tuple(response)
	cleanup(response)
	return response

def serve_asset(request):
	path = request.path[len(config.customization.asset_route_prefix) + 1:]
	#	TODO: check cache control

	asset_data = retrieve_asset(path)
	if asset_data is None:
		if path.endswith('.css'):
			asset_data = retrieve_asset(path.replace('.css', '.less'), True)
		if path.endswith('.js'):
			asset_data = retrieve_asset(path.replace('.js', '.jsx'), True)
	if asset_data is None:
		raise NotFound(request.path)
	
	mimetype = types_map.get('.%s'%path.split('.')[-1], 'text/plain')
	#	TODO: add cache control
	return BaseResponse(
		response=asset_data,
		status=200,
		mimetype=mimetype
	)

def handle_request(environ, start_response):
	request = BaseRequest(environ)
	route = request.path

	if route.startswith('/%s'%config.customization.asset_route_prefix):
		try:
			response = serve_asset(request)
		except HTTPException as ex:
			report_error(ex)
			response = parse_response_tuple(ex.response())
	else:
		try:
			response = serve_controller(request)
		except HTTPException as ex:
			report_error(ex)
			
			if len(ex.diag) > 1:
				source_ex, context = ex.diag
			else:
				source_ex, *empty = ex.diag
				context = None
			response = parse_response_tuple(get_error_response(ex, source_ex, route, request.method.lower(), context))
	
	response.headers['Server'] = _identifier
	return response(environ, start_response)
