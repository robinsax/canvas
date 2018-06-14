# coding: utf-8
'''
The immediate logic surrounding request receiving and response dispatch. The
function `handle_request` in this module is canvas's WSGI application.
'''

import time
import platform

from datetime import datetime
from werkzeug import BaseRequest, BaseResponse
from werkzeug.contrib.securecookie import SecureCookie

from ..exceptions import HTTPException, InternalServerError, NotFound, \
	UnsupportedVerb, OversizeEntity, UnsupportedMediaType
from ..utils import logger, format_exception, create_callback_registrar
from ..configuration import config
from ..dictionaries import AttributedDict, RequestParameters
from .controllers import Endpoint
from .model import create_session
from .plugins import get_path_occurrences
from .routing import RouteString, resolve_route
from .request_parsers import parse_request_body
from .request_context import RequestContext
from .request_errors import get_error_response
from .responses import create_json
from .assets import get_asset
from .. import __version__ as canvas_version

#	Define the value for the server header.
__server__ = 'canvas/%s Python/%s'%(canvas_version, platform.python_version())

#	Create a logger.
log = logger(__name__)
#	Define the request handling kickoff callback. 
on_request_received = create_callback_registrar()

def parse_response_tuple(tpl):
	'''Transform a response scalar or tuple to a respose object.'''
	#	Tuplize.
	if not isinstance(tpl, (list, tuple)):
		tpl = (tpl,)
	
	#	Fill incompelete values.
	corrected = [str(), 200, dict(), 'text/plain']
	for i in range(len(tpl)):
		corrected[i] = tpl[i]
	
	#	Unpack and return.
	data, status, headers, mimetype = corrected
	if headers is None:
		headers = dict()

	return BaseResponse(
		response=data,
		status=status,
		headers=headers,
		mimetype=mimetype
	)

def serve_controller(request):
	'''Serve a controller response.'''
	#	Resolve the request route.
	route = request.path
	controller, variables = resolve_route(route)
	#	Resolve the request verb.
	verb = request.method.lower()
	if verb not in controller.__verbs__:
		#	This controller doesn't support that verb.
		raise UnsupportedVerb(verb, [v.upper() for v in controller.__verbs__])
	#	Retrieve the handler method.
	handler = getattr(controller, ''.join(('on_', verb)))

	#	Resolve parameters.
	query_parameters, request_parameters = (
		RequestParameters(request.args), None
	)
	#	Read body if there is one.
	if verb != 'get':
		#	Retrieve body properties.
		body_size, content_type = (
			int(request.headers.get('Content-Length', 0)), 
			request.headers.get('Content-Type')
		)
		#	Assert size is safe.
		if body_size > config.security.max_bytes_receivable:
			raise OversizeEntity(body_size)
		
		if body_size == 0:
			#	If controller has default expectation, empty bodies have are
			#	an empty parameter set.
			if 'json' in controller.__expects__:
				request_parameters = RequestParameters()
		else:
			#	If it should be asserted, assert the content type is correct.
			should_assert = content_type and controller.__expects__ != '*'
			if should_assert and controller.__expects__ not in content_type:
				raise UnsupportedMediaType(
					' '.join(('Expected', controller.__expects__.upper()))
				)

			#	Read the charset definition if there is one.
			charset = 'utf-8'
			if ';' in content_type:
				content_type, charset = content_type.split(';')
			
			#	Parse the request parameters.
			request_parameters = parse_request_body(
				request.get_data(as_text=True), content_type, charset
			)
	query_parameters.propagate_and_lock()
	if isinstance(request_parameters, RequestParameters):
		request_parameters.propagate_and_lock()

	#	Resolve the cookie.
	cookie_key, secret = (
		config.security.cookie_key, 
		config.security.cookie_secret.encode('utf-8')
	)
	cookie_data = request.cookies.get(cookie_key, None)
	if cookie_data:
		cookie = SecureCookie.unserialize(cookie_data, secret)
	else:
		cookie = SecureCookie(secret_key=secret)
	
	#	Create and associate the request context.
	context = RequestContext(
		cookie=cookie,
		session=create_session(),
		request=request_parameters,
		query=query_parameters,
		headers=request.headers,
		route=RouteString(route, variables),
		verb=verb,
		url=request.url,
		__controller__=controller
	)
	RequestContext.put(context)

	#	Define a cleanup callback.
	def cleanup(response=None):
		#	Disassociate request context.
		RequestContext.pop()

		#	Save the cookie if applicable.
		if response and cookie.should_save:
			response.set_cookie(cookie_key, cookie.serialize())
	
	try:
		#	Invoke request handling kickoff callbacks.
		on_request_received.invoke(context)
		#	Invoke the handler.
		response = handler(context)
	except BaseException as ex:
		#	Ensure the exception is an HTTP exception and reraise
		http_ex = ex
		if not isinstance(ex, HTTPException):
			http_ex = InternalServerError(ex)
		http_ex.context = context
		raise http_ex from ex
	
	#	Clean up and return parsed response.
	response = parse_response_tuple(response)
	cleanup(response)
	return response
  
def serve_asset(request):
	'''Serve an asset with cache control or a 304.'''
	#	TODO: Revving support.
	#	Retrieve the requested asset.
	asset = get_asset(
		request.path[len(config.customization.asset_route_prefix) + 1:]
	)
	#	Assert it exists.
	if asset is None:
		raise NotFound(request.path)

	#	Run cache check.
	if 'If-Modified-Since' in request.headers:
		cache_time = datetime.strptime(request.headers['If-Modified-Since'], 
				'%a, %d %b %Y %H:%m:%S GMT')
		if asset.mtime <= cache_time:
			return BaseResponse(status=304)
	
	#	Return the asset.
	return BaseResponse(
		response=asset.data,
		status=200,
		mimetype=asset.mimetype,
		headers={
			'Cache-Control': 'max-age=0, must-revalidate',
			'Last-Modified': asset.mtime.strftime('%a, %d %b %Y %H:%m:%S GMT')
		}
	)

def handle_request(environ, start_response):
	'''The WSGI application.'''
	#	Read the request.
	request = BaseRequest(environ)
	route = request.path

	if route.startswith('/%s'%config.customization.asset_route_prefix):
		#	Serve an asset.
		try:
			response = serve_asset(request)
		except HTTPException as ex:
			#	Report if configured to do so.
			ex.maybe_report(log)
			#	Return a barebones error response.
			response = parse_response_tuple(ex.simple_response())
		except BaseException as ex:
			log.critical(format_exception(ex))
			response = parse_response_tuple((
				'Internal Server Error', 500
			))
	else:
		#	Serve a controller.
		try:
			response = serve_controller(request)
		except HTTPException as ex:
			#	Report if configured to do so.
			ex.maybe_report(log)
			#	Check for a source exception beneath this one.
			source_ex = ex
			if isinstance(ex, InternalServerError) and ex.reraised_from:
				source_ex = ex.reraised_from
			
			#	Create the appropriate error response.
			response = parse_response_tuple(
				get_error_response(ex, source_ex, route, request.method.lower(), ex.context)
			)
	
	#	Identify self.
	response.headers['Server'] = __server__
	return response(environ, start_response)
