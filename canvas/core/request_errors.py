#	coding utf-8
'''
Graceful controller service error handling.
'''

from ..controllers import Endpoint
from ..configuration import config
from ..utils import format_exception
from .json_io import serialize_json
from .responses import create_json, create_webpage

def get_error_response(route, ex, context=None):
	error_data = {
		'code': ex.status_code,
		'title': ex.title
	}
	if config.development.debug:
		error_data['debug_info'] = {
			'traceback': format_exception(ex).strip(),
			'context': None if context is None else serialize_json(context, fallback=repr)
		}
	
	api_route = '/%s'%config.customization.api_route_prefix
	if route.startswith(api_route):
		return create_json('failure', error_data, **{
			'code': ex.status_code,
			'headers': ex.headers
		})
	else:
		return create_webpage('error.html', {
			'error': error_data
		}, code=ex.status_code, headers=ex.headers)
