#	coding utf-8
'''
Graceful controller service error handling.
'''

from ..configuration import config
from ..utils import format_exception
from ..callbacks import define_callback_type, invoke_callbacks
from .dictionaries import LazyAttributedDict
from .json_io import serialize_json
from .responses import create_json, create_page

define_callback_type('error', (LazyAttributedDict,), ext=True)

def get_error_response(http_ex, source_ex, route, verb, context):
	error_dict = {
		'code': http_ex.status_code,
		'title': http_ex.title,
	}
	description = str(http_ex)
	if description:
		error_dict['description'] = description

	if config.development.debug:
		error_dict['debug_info'] = {
			'traceback': format_exception(source_ex).strip(),
			'context': None if context is None else serialize_json(context, fallback=repr)
		}
	
	in_api_realm = route.startswith('/%s'%config.customization.api_route_prefix)

	error_data = LazyAttributedDict({
		'response': None,
		'in_api_realm': in_api_realm,
		'http_ex': http_ex,
		'source_ex': source_ex,
		'route': route,
		'error_dict': error_dict,
		'context': context
	})
	
	invoke_callbacks('error', error_data)
	if error_data.response:
		return error_data.response
	
	if in_api_realm or verb != 'get':
		return create_json('error', error_dict, **{
			'code': http_ex.status_code,
			'headers': http_ex.headers
		})
	else:
		return create_page('error.html', {
			'__route__': route,
			'error': error_dict
		}, code=http_ex.status_code, headers=http_ex.headers)
