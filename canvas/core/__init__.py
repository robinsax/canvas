#	coding utf-8
'''
Core functionality including plugin management, 
request handling, and asset management.
'''

from ..exceptions import _Redirect
from .. import register

from .request_handler import handle_request
from .thread_context import get_thread_context

__all__ = [
	'asset_url',
	'redirect_to',
	'get_thread_context'
]

@register('template_global')
def asset_url(rel_path):
	'''
	Return the URL relative to domain root for 
	an asset.
	'''
	if rel_path.startswith('/'):
		return f'/assets{rel_path}'
	return f'/assets/{rel_path}'

def redirect_to(target, code=302):
	'''
	Redirect the view to `target`. You do not need 
	to return the result; internally, a `_Redirect` 
	is raised and handled.
	:target The redirect target
	:code The HTTP redirect code, default `302`
	'''
	raise _Redirect(target, code)

def flash_message(message):
	'''
	Flash a message the next time a view or view
	update is sent.
	'''
	get_thread_context()['__flash__'] = message

@register('template_global')
def get_flash_message():
	return get_thread_context().get('__flash__', None)
