#	coding utf-8
'''
The canvas WSGI application implementation.
'''

from traceback import format_tb
from werkzeug import BaseRequest, BaseResponse

from ..exceptions import (
	HTTPException, 
	NotFound,
	UnsupportedVerb
)
from . import _route_map

def serve_controller(request):
	path = request.path
	if path not in _route_map:
		raise NotFound(path)
	controller = _route_map[path]

	verb = request.method.lower()
	if verb not in controller.__verbs__:
		raise UnsupportedVerb(verb, [v.upper() for v in controller.__verbs__])
	handler = getattr(controller, 'do_{}'.format(verb))

	return handler(dict())

def correct_response_tuple(tpl):
	if not isinstance(tpl, (list, tuple)):
		tpl = (tpl,)
	
	corrected = ['', 200, None, 'text/plain']
	count = len(tpl)
	for i in range(4):
		if count < i + 1:
			return corrected
		corrected[i] = tpl[i]
	return corrected

def report_error(ex):
	traceback = (''.join(format_tb(ex.__traceback__))).strip().replace('\n    ', '\n\t').replace('\n  ', '\n')
	print(f'{ex.__class__.__name__}: {ex}\n{traceback}')

def handle_request(environ, start_response):
	request = BaseRequest(environ)

	try:
		response = serve_controller(request)
	except HTTPException as ex:
		if ex.status_code > 499:
			report_error(ex)
		response = ex.response()
	except BaseException as ex:
		report_error(ex)
		response = ('Internal Server Error', 500, None, 'text/plain')
	
	data, status, headers, mimetype = correct_response_tuple(response)
	if headers is None:
		headers = dict()
	
	response_object = BaseResponse(**{
		'response': data,
		'status': status,
		'headers': headers,
		'mimetype': mimetype
	})
	return response_object(environ, start_response)
