# coding: utf-8
'''
Response generation function definitions for common cases.
'''

from ..json_io import serialize_json
from .request_context import RequestContext

def create_json(status, data=None, code=200, headers=None):
	'''
	Return a canonical JSON response of the status `status` and data `data.`
	'''
	if data is not None:
		body = serialize_json({'status': status, 'data': data})
	else:
		body = serialize_json({'status': status})
	
	return body, code, headers, 'application/json'

def create_redirect(target_url, code=302, headers=dict()):
	'''
	Return a redirect response tuple. Non-standardly, the response to any kind 
	of asynchronoous request can trigger a redirect.
	'''
	#	Retrieve the context and check if this is a view request.
	is_view_request, context = RequestContext.get(), False
	if context:
		is_view_request = context.headers.get('X-cv-View') == '1'

	headers['Location'] = target_url
	if is_view_request:
		#	Return control JSON and a redirect.
		return create_json('action', {
			'action': 'redirect'
		}, code, headers)
	else:
		#	Return a basic redirect.
		return None, code, headers, None

def create_page(view, code=200, headers=None):
	'''
	Render `view` and return an HTML response tuple.
	'''
	html = ''.join(('<!DOCTYPE html>\n', view.render()))
	return html, code, headers, 'text/html'
