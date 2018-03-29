#	coding utf-8
'''
Response generation methods.
'''

from ..namespace import export
from .json_io import serialize_json
from .request_context import RequestContext
from .templates import render_template

@export
def create_json(status, data=None, code=200, headers=None):
	if data:
		body = serialize_json({
			'status': status,
			'data': data
		})
	else:
		body = serialize_json({'status': status})
	return body, code, headers, 'application/json'

@export
def create_redirect(target_url, code=302, headers=dict()):
	is_view_request = False

	context = RequestContext.get()
	if context:
		is_view_request = context.headers.get('X-cv-View') == '1'

	if is_view_request:
		return create_json('status', {
			'action': 'redirect',
			'url': target_url
		})
	else:
		headers['Location'] = target_url
		return None, code, headers, None

@export
def create_webpage(template_path, params=dict(), code=200, headers=dict()):
	rendered_template = render_template(template_path, params)
	return rendered_template, code, headers, 'text/html'
