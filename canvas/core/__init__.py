#	coding utf-8
'''
Core functionality including request handling,
plugin management, and asset management.
'''

import json

from ..exceptions import _Redirect
from ..utils.registration import register

from .thread_context import get_thread_context
from .assets import *

#	Declare exports.
__all__ = [
	'asset_url',
	'create_json',
	'redirect_to',
	'get_thread_context',
	'flash_message',
	#	Assets subpackage.
	'render_template'
]

def create_json(status_str, *data, status=200, headers={}, default_serializer=None):
	'''
	Create a JSON response tuple in the canonical format.

	:status_str The status string. Should be one of: `'success'`, 
		`'failure'`, or `'error'`.
	:data (Optional) A data package.
	:status The HTTP status code for the response.
	:headers A dictionary of headers for the response.
	:default_serializer A fallback serialization function for 
		complex objects.
	'''
	if len(data) > 0:
		#	Include a data package.
		return json.dumps({
			'status': status_str,
			'data': data[0]
		}, default=default_serializer), status, headers, 'application/json'
	else:
		#	Don't include a data package.
		return json.dumps({
			'status': status_str
		}, default=default_serializer), status, headers, 'application/json'

#	`create_json()` is required by the 
#	request handler.
from .request_handler import handle_request

@register.template_helper
def asset_url(rel_path):
	'''
	Return the URL relative to domain root for an asset. 
	This message should always be called for asset 
	retrieval to allow for forwards-compatability.
	'''
	if rel_path.startswith('/'):
		return f'/assets{rel_path}'
	return f'/assets/{rel_path}'

def redirect_to(target, code=302):
	'''
	Redirect the view to `target`. Does not return
	a value. When called, flow control is halted.

	`code` will be ignored if an AJAX POST request
	is being handled; The redirection will be formulated
	as a view action (it wouldn't work otherwise).

	:target The URL to redirect to.
	:code The HTTP redirect code. Must be 3xx.
	'''
	raise _Redirect(target, code)

def flash_message(message):
	'''
	Flash a message the next time a view or view
	update is sent.
	'''
	get_thread_context()['__flash__'] = message

@register.template_helper
def get_flash_message():
	'''
	Return the currently queued flash message, or
	`None` if there isn't one.
	'''
	return get_thread_context().get('__flash__', None)
